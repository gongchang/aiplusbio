import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import re
import time
import schedule
import threading
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import logging

class EventScraper:
    def __init__(self, database):
        self.db = database
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load websites to watch
        self.websites = self.load_websites()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_websites(self) -> List[str]:
        """Load websites from the text file"""
        try:
            with open('websites_to_watch.txt', 'r') as f:
                websites = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return websites
        except FileNotFoundError:
            self.logger.error("websites_to_watch.txt not found")
            return []
    
    def scrape_all_sites(self) -> List[Dict[str, Any]]:
        """Scrape all websites and return new events"""
        all_new_events = []
        
        for website in self.websites:
            try:
                self.logger.info(f"Scraping {website}")
                events = self.scrape_website(website)
                all_new_events.extend(events)
                
                # Log successful scraping
                self.db.log_scraping(website, 'success', len(events))
                
                # Be respectful with delays
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error scraping {website}: {str(e)}")
                self.db.log_scraping(website, 'error', 0, str(e))
        
        return all_new_events
    
    def scrape_website(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single website for events"""
        events = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Try different scraping strategies based on URL patterns
            if 'calendar' in url.lower() or 'events' in url.lower():
                events = self.scrape_calendar_page(response.text, url)
            elif 'rss' in url.lower() or 'feed' in url.lower():
                events = self.scrape_rss_feed(response.text, url)
            else:
                events = self.scrape_generic_page(response.text, url)
            
            # Add events to database
            new_events = []
            for event in events:
                event_id = self.db.add_event(event)
                if event_id:
                    event['id'] = event_id
                    new_events.append(event)
            
            return new_events
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return []
    
    def scrape_calendar_page(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Scrape calendar-style event pages"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Common selectors for event elements
        event_selectors = [
            '.event', '.calendar-event', '.event-item', '.event-card',
            '[class*="event"]', '[class*="calendar"]', 'article', '.entry'
        ]
        
        for selector in event_selectors:
            event_elements = soup.select(selector)
            if event_elements:
                for element in event_elements:
                    event = self.extract_event_from_element(element, source_url)
                    if event:
                        events.append(event)
                break
        
        return events
    
    def scrape_rss_feed(self, content: str, source_url: str) -> List[Dict[str, Any]]:
        """Scrape RSS/Atom feeds"""
        events = []
        
        try:
            feed = feedparser.parse(content)
            
            for entry in feed.entries:
                event = {
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source_url': source_url,
                    'date': self.extract_date_from_text(entry.get('published', '')),
                    'time': self.extract_time_from_text(entry.get('published', '')),
                    'location': '',
                    'is_virtual': self.detect_virtual_event(entry.get('title', '') + ' ' + entry.get('summary', '')),
                    'requires_registration': self.detect_registration_required(entry.get('title', '') + ' ' + entry.get('summary', '')),
                    'categories': []
                }
                
                if event['title'] and event['date']:
                    events.append(event)
        
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed: {str(e)}")
        
        return events
    
    def scrape_generic_page(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Scrape generic pages for events"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Look for date patterns in the page
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        # Find elements containing dates
        for pattern in date_patterns:
            date_elements = soup.find_all(text=re.compile(pattern, re.IGNORECASE))
            
            for element in date_elements:
                parent = element.parent
                if parent:
                    event = self.extract_event_from_element(parent, source_url)
                    if event:
                        events.append(event)
        
        return events
    
    def extract_event_from_element(self, element, source_url: str) -> Dict[str, Any]:
        """Extract event information from a DOM element"""
        try:
            # Extract title
            title = ''
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.event-title', '[class*="title"]']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = element.get_text(strip=True)[:100]  # Fallback
            
            # Extract description
            description = ''
            desc_selectors = ['.description', '.summary', '.content', 'p']
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break
            
            # Extract date
            date_text = element.get_text()
            date = self.extract_date_from_text(date_text)
            
            # Extract time
            time_text = element.get_text()
            time = self.extract_time_from_text(time_text)
            
            # Extract location
            location = ''
            location_selectors = ['.location', '.venue', '.address', '[class*="location"]']
            for selector in location_selectors:
                loc_elem = element.select_one(selector)
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    break
            
            # Extract URL
            url = source_url
            link_elem = element.find('a')
            if link_elem and link_elem.get('href'):
                url = urljoin(source_url, link_elem.get('href'))
            
            # Detect virtual/registration
            full_text = element.get_text()
            is_virtual = self.detect_virtual_event(full_text)
            requires_registration = self.detect_registration_required(full_text)
            
            if title and date:
                return {
                    'title': title,
                    'description': description,
                    'date': date,
                    'time': time,
                    'location': location,
                    'url': url,
                    'source_url': source_url,
                    'is_virtual': is_virtual,
                    'requires_registration': requires_registration,
                    'categories': []
                }
        
        except Exception as e:
            self.logger.error(f"Error extracting event: {str(e)}")
        
        return None
    
    def extract_date_from_text(self, text: str) -> str:
        """Extract date from text using various patterns"""
        # Common date patterns
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
            (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', '%B %d %Y'),
            (r'(\d{1,2})\s+(\w+)\s+(\d{4})', '%d %B %Y')
        ]
        
        for pattern, format_str in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if format_str == '%m/%d/%Y':
                        date_str = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
                    elif format_str == '%Y-%m-%d':
                        date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    elif format_str == '%B %d %Y':
                        date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    elif format_str == '%d %B %Y':
                        date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    
                    parsed_date = datetime.strptime(date_str, format_str)
                    
                    # Only return future dates
                    if parsed_date.date() >= datetime.now().date():
                        return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return ''
    
    def extract_time_from_text(self, text: str) -> str:
        """Extract time from text"""
        # Time patterns
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(AM|PM)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*(AM|PM)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ''
    
    def detect_virtual_event(self, text: str) -> bool:
        """Detect if an event is virtual"""
        virtual_keywords = [
            'virtual', 'online', 'zoom', 'webinar', 'webcast', 'streaming',
            'remote', 'digital', 'live stream', 'livestream'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in virtual_keywords)
    
    def detect_registration_required(self, text: str) -> bool:
        """Detect if registration is required"""
        registration_keywords = [
            'register', 'registration', 'rsvp', 'sign up', 'signup',
            'required', 'mandatory', 'book', 'reserve'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in registration_keywords)
    
    def start_background_scraping(self):
        """Start background scraping scheduler"""
        # Schedule scraping every 6 hours
        schedule.every(6).hours.do(self.scrape_all_sites)
        
        # Run scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("Background scraping scheduler started") 