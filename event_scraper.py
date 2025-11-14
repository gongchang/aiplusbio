import requests
from bs4 import BeautifulSoup
import json
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Handle SSL certificate issues
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.detail_cache = {}
        
        # Load websites to watch
        self.websites = self.load_websites()
    
    def get_institution(self, source_url: str) -> str:
        """Determine institution based on URL"""
        if ('mit.edu' in source_url or 
            'broadinstitute' in source_url or 
            'iaifi.org' in source_url or 
            'ericandwendyschmidtcenter.org' in source_url):
            return 'MIT'
        elif 'harvard' in source_url:
            return 'Harvard'
        elif 'bu.edu' in source_url:
            return 'BU'
        elif 'brown.edu' in source_url:
            return 'Brown'
        else:
            return 'Others'
    
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
        
        # After scraping, attempt to enrich metadata for existing events that still need details
        try:
            self.refresh_event_metadata(days_ahead=180, include_past=False, lookback_days=90, max_events=100)
        except Exception as e:
            self.logger.debug(f"Metadata refresh skipped due to error: {e}")
        
        return all_new_events
    
    def scrape_website(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single website for events"""
        events = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Try different scraping strategies based on URL patterns
            # Check for site-specific scrapers first
            if any(pattern in url.lower() for pattern in ['bu.edu/hic', 'math.mit.edu/crib', 'bu.edu/csmet', 'brown.edu/ccmb', 'media.mit.edu/events', 'broadinstitute.org']):
                events = self.scrape_calendar_page(response.text, url)
            elif 'calendar' in url.lower() or 'events' in url.lower():
                events = self.scrape_calendar_page(response.text, url)
            elif 'rss' in url.lower() or 'feed' in url.lower():
                events = self.scrape_rss_feed(response.text, url)
            else:
                events = self.scrape_generic_page(response.text, url)
            
            # Enrich and clean events before saving
            processed_events = []
            for raw_event in events:
                processed = self.post_process_event(raw_event)
                if processed:
                    processed_events.append(processed)
            events = processed_events

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
        """Scrape calendar-style event pages with improved element detection"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Try specific site patterns first
        if 'iaifi.org' in source_url:
            # Special handling for iaifi.org which uses <li> elements with structured content
            li_elements = soup.find_all('li')
            for li in li_elements:
                text = li.get_text()
                # Look for the specific pattern: "Friday, September 26, 2025, 2:00pm–3:00pm"
                if re.search(r'\b(Friday|Monday|Tuesday|Wednesday|Thursday|Saturday|Sunday)', text, re.IGNORECASE) and re.search(r'\d{1,2}:\d{2}[ap]m', text, re.IGNORECASE):
                    event = self.extract_event_from_element(li, source_url, soup)
                    if event:
                        events.append(event)
        
        elif 'be.mit.edu' in source_url:
            # Special handling for be.mit.edu seminars
            # Look for elements containing "Start Time:" or time patterns
            elements = soup.find_all(['div', 'span', 'p'], text=re.compile(r'Start Time:|12:00PM|1:00PM|2:00PM|3:00PM|4:00PM', re.I))
            for element in elements:
                # Get the parent container
                parent = element.parent
                while parent and parent.name not in ['div', 'article', 'section']:
                    parent = parent.parent
                if parent:
                    event = self.extract_event_from_element(parent, source_url, soup)
                    if event:
                        events.append(event)
        
        elif 'events.seas.harvard.edu' in source_url:
            # Special handling for Harvard SEAS events
            # Look for elements with date and time patterns
            elements = soup.find_all(['div', 'article'], class_=re.compile(r'event|item', re.I))
            for element in elements:
                text = element.get_text()
                if re.search(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+\w+\s+\d{1,2}', text, re.I) and re.search(r'\d{1,2}[ap]m', text, re.I):
                    event = self.extract_event_from_element(element, source_url, soup)
                    if event:
                        events.append(event)
        
        elif 'ericandwendyschmidtcenter.org' in source_url:
            # Special handling for Schmidt Center events
            # Look for elements with "Monday, November 3, 20254:00 pm" pattern
            elements = soup.find_all(['div', 'article', 'li'])
            for element in elements:
                text = element.get_text()
                if re.search(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+\s+\d{1,2},\s+\d{4}\d{1,2}:\d{2}\s*[ap]m', text, re.I):
                    event = self.extract_event_from_element(element, source_url, soup)
                    if event:
                        events.append(event)
        
        elif 'bu.edu/hic/noteworthy/calendar' in source_url:
            # Special handling for BU HIC calendar
            events.extend(self.scrape_bu_hic_calendar(soup, source_url))
        
        elif 'math.mit.edu/crib' in source_url:
            # Special handling for MIT CRIB
            events.extend(self.scrape_mit_crib(soup, source_url))
        
        elif 'bu.edu/csmet/research' in source_url:
            # Special handling for BU CSMET seminar
            events.extend(self.scrape_bu_csmet_seminar(soup, source_url))
        
        elif 'events.brown.edu/ccmb' in source_url:
            # Special handling for Brown CCMB
            events.extend(self.scrape_brown_ccmb(soup, source_url))
        
        elif 'media.mit.edu/events' in source_url:
            # Special handling for MIT Media Lab
            events.extend(self.scrape_mit_media_lab(soup, source_url))
        
        elif 'events.broadinstitute.org' in source_url:
            # Special handling for Broad Institute
            events.extend(self.scrape_broad_institute(soup, source_url))
        
        # Common selectors for event elements
        event_selectors = [
            '.event', '.calendar-event', '.event-item', '.event-card',
            '[class*="event"]', '[class*="calendar"]', 'article', '.entry'
        ]
        
        # Only use generic selectors if we didn't find events with specific patterns
        if not events:
            for selector in event_selectors:
                event_elements = soup.select(selector)
                if event_elements:
                    for element in event_elements:
                        event = self.extract_event_from_element(element, source_url, soup)
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
                    event = self.extract_event_from_element(parent, source_url, soup)
                    if event:
                        events.append(event)
        
        return events
    
    def extract_event_from_element(self, element, source_url: str, soup: BeautifulSoup = None) -> Dict[str, Any]:
        """Extract event information from a DOM element with improved logic"""
        try:
            if self.is_placeholder_element(element):
                return None
            
            # Extract title with better logic
            title = self.extract_better_title(element)
            
            # Extract description
            description = self.extract_description(element)
            
            # Extract date and time
            date_text = element.get_text()
            date = self.extract_date_from_text(date_text)
            # Prefer structured time extraction within element or page-level JSON-LD
            time = self.extract_time_from_element(element, soup) or self.extract_time_from_text(date_text)
            
            # Extract location
            location = self.extract_location(element)
            
            # Extract URL with improved logic
            url = self.extract_best_event_url(element, source_url, title)
            
            # Detect virtual/registration
            full_text = element.get_text()
            is_virtual = self.detect_virtual_event(full_text)
            requires_registration = self.detect_registration_required(full_text)
            
            if title and date and not self.is_date_time_title(title):
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
    def format_time_hhmm_ampm(self, dt: datetime) -> str:
        """Format a datetime to 'H:MM AM/PM'"""
        hour = dt.hour
        minute = dt.minute
        ampm = 'AM'
        if hour == 0:
            display_hour = 12
        elif hour == 12:
            display_hour = 12
            ampm = 'PM'
        elif hour > 12:
            display_hour = hour - 12
            ampm = 'PM'
        else:
            display_hour = hour
        return f"{display_hour}:{minute:02d} {ampm}"

    def extract_time_from_element(self, element, soup: BeautifulSoup = None) -> str:
        """Try to extract a start time from structured markup within the element or page.
        Checks:
        - <time datetime="...">
        - meta itemprop="startDate" content="..."
        - JSON-LD script blocks with Event.startDate
        Returns canonical 'H:MM AM/PM' or ''
        """
        # 1) time tags within element
        for t in element.find_all('time'):
            dt_attr = t.get('datetime') or t.get('content')
            txt = t.get_text(strip=True)
            iso = dt_attr or ''
            # If datetime ISO present, parse
            if iso:
                try:
                    # Support '2025-09-08T14:00:00-04:00'
                    dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
                    return self.format_time_hhmm_ampm(dt)
                except Exception:
                    pass
            # else try text fallback
            if txt:
                v = self.extract_time_from_text(txt)
                if v:
                    return v

        # 2) itemprop/meta
        meta = element.find(attrs={'itemprop': 'startDate'})
        if meta:
            iso = meta.get('content') or meta.get('datetime') or meta.get('value')
            if iso:
                try:
                    dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
                    return self.format_time_hhmm_ampm(dt)
                except Exception:
                    pass

        # 3) JSON-LD at page level (first Event found)
        if soup is not None:
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or '')
                except Exception:
                    continue
                # Handle list or single object
                objs = data if isinstance(data, list) else [data]
                for obj in objs:
                    if not isinstance(obj, dict):
                        continue
                    # Events may be nested
                    candidates = []
                    if obj.get('@type') == 'Event':
                        candidates.append(obj)
                    for key in ('@graph', 'events', 'event'):
                        val = obj.get(key)
                        if isinstance(val, list):
                            candidates.extend([x for x in val if isinstance(x, dict) and x.get('@type') == 'Event'])
                    for ev in candidates:
                        start = ev.get('startDate') or ev.get('startTime')
                        if start:
                            try:
                                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                                return self.format_time_hhmm_ampm(dt)
                            except Exception:
                                continue
        return ''
    

    def extract_better_title(self, element) -> str:
        """Extract title with improved logic to avoid date/time titles"""
        
        # Special handling for iaifi.org structure
        if element.name == 'li':
            # Look for <em> tags which contain the talk titles
            em_tag = element.find('em')
            if em_tag:
                title = em_tag.get_text(strip=True)
                if title and not self.is_date_time_title(title):
                    return title
            
            # Look for speaker names in <strong> tags with links
            strong_tag = element.find('strong')
            if strong_tag:
                # Extract speaker name from the link text
                link = strong_tag.find('a')
                if link:
                    speaker_name = link.get_text(strip=True)
                    if speaker_name and not self.is_date_time_title(speaker_name):
                        return speaker_name
        
        # Try specific title selectors first
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5',
            '.title', '.event-title', '.event-name',
            '[class*="title"]', '[class*="event-title"]',
            '.headline', '.event-headline', 'em'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and not self.is_date_time_title(title):
                    return title
        
        # Try to find title in description or other text elements
        desc_selectors = ['.description', '.summary', '.content', 'p', '.event-description']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                # Look for the first sentence that looks like a title
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if (len(sentence) > 10 and len(sentence) < 200 and 
                        not self.is_date_time_title(sentence)):
                        return sentence
        
        # Last resort: try to extract meaningful text from the element
        full_text = element.get_text(strip=True)
        lines = full_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and len(line) < 200 and 
                not self.is_date_time_title(line)):
                return line
        
        return ""
    
    def extract_description(self, element) -> str:
        """Extract description from element"""
        desc_selectors = ['.description', '.summary', '.content', 'p', '.event-description']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(strip=True)
        return ""
    
    def extract_location(self, element) -> str:
        """Extract location from element"""
        location_selectors = ['.location', '.venue', '.address', '[class*="location"]']
        for selector in location_selectors:
            loc_elem = element.select_one(selector)
            if loc_elem:
                return loc_elem.get_text(strip=True)
        return ""
    
    def extract_best_event_url(self, element, source_url: str, title: str) -> str:
        """Extract the most relevant URL for the event"""
        
        # Find all links in the element
        links = element.find_all('a', href=True)
        
        if not links:
            return source_url
        
        # Score each link based on relevance
        best_url = source_url
        best_score = 0
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            link_title = link.get('title', '').lower()
            
            # Skip empty or invalid URLs
            if not href or href.startswith('#'):
                continue
            
            # Build full URL
            full_url = urljoin(source_url, href)
            
            # Score the link
            score = 0
            
            # Higher score for links that contain event-related keywords
            event_keywords = ['event', 'detail', 'more', 'read', 'learn', 'register', 'rsvp']
            for keyword in event_keywords:
                if keyword in link_text or keyword in link_title:
                    score += 2
            
            # Higher score for links that contain words from the event title
            if title:
                title_words = title.lower().split()
                for word in title_words:
                    if len(word) > 3 and (word in link_text or word in link_title):
                        score += 1
            
            # Higher score for links that look like event detail pages
            url_lower = full_url.lower()
            if any(pattern in url_lower for pattern in ['/event/', '/events/', '/detail', '/view']):
                score += 3
            
            # Lower score for generic navigation links
            generic_patterns = ['/about', '/contact', '/home', '/index', '/news', '/blog']
            if any(pattern in url_lower for pattern in generic_patterns):
                score -= 2
            
            # Prefer links with meaningful text over generic ones
            if len(link_text) > 5 and link_text not in ['click here', 'read more', 'learn more']:
                score += 1
            
            # Update best URL if this one has a higher score
            if score > best_score:
                best_score = score
                best_url = full_url
        
        return best_url
    
    def is_date_time_title(self, text: str) -> bool:
        """Check if text looks like a date/time instead of a title"""
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Check for date/time patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}',
            r'\d{1,2}:\d{2}\s*(am|pm)',
            r'@\s*\d{1,2}:\d{2}',
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check if text is mostly numbers and common date/time words
        words = text.split()
        if len(words) <= 3:
            date_time_words = ['am', 'pm', 'at', '@', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
            date_time_count = sum(1 for word in words if word.lower() in date_time_words or word.isdigit())
            if date_time_count >= len(words) * 0.7:  # 70% or more are date/time words
                return True
        
        return False
    
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
        """Extract and normalize a start time from text.
        Returns a canonical 12-hour format like '2:00 PM' when found, else ''.
        """
        if not text:
            return ''

        s = text
        # Normalize different dash types and remove parentheses/timezone noise
        s = re.sub(r'[\u2013\u2014–—]', '-', s)
        s = re.sub(r'\((?:[^()]*?)\)', ' ', s)
        s = re.sub(r'\b(ET|EST|EDT|Eastern Time|Eastern|Boston Time|GMT|UTC)\b', ' ', s, flags=re.IGNORECASE)

        # If it's a range like "2 pm - 3 pm", only take the first part
        if '-' in s:
            s = s.split('-')[0].strip()

        candidates = []

        # 1) explicit 12h with am/pm (spaces or attached), optional minutes; also accept single A/P
        for m in re.finditer(r'\b(\d{1,2})(?::(\d{2}))?\s*([ap])m?\b', s, flags=re.IGNORECASE):
            hour = int(m.group(1))
            minute = int(m.group(2) or '0')
            ampm = ('AM' if m.group(3).lower() == 'a' else 'PM')
            if hour == 12:
                hour24 = 0
            else:
                hour24 = hour
            if ampm == 'PM':
                hour24 += 12
            candidates.append((hour24, minute))

        # 2) attached am/pm like '2pm' or '1030am' or single '2p'
        for m in re.finditer(r'\b(\d{1,2})(\d{2})?([ap])m?\b', s, flags=re.IGNORECASE):
            hour = int(m.group(1))
            minute = int(m.group(2) or '0')
            ampm = ('AM' if m.group(3).lower() == 'a' else 'PM')
            if hour == 12:
                hour24 = 0
            else:
                hour24 = hour
            if ampm == 'PM':
                hour24 += 12
            candidates.append((hour24, minute))

        # 3) 24-hour times like '14:00'
        for m in re.finditer(r'\b(\d{1,2}):(\d{2})\b', s):
            hour24 = int(m.group(1))
            minute = int(m.group(2))
            # Only accept reasonable 24-hour times
            if 0 <= hour24 <= 23 and 0 <= minute <= 59:
                candidates.append((hour24, minute))

        # 4) Compact formats like '12:00P' or '2:00P', '4:00A'
        for m in re.finditer(r'\b(\d{1,2}):(\d{2})([AP])\b', s):
            hour = int(m.group(1))
            minute = int(m.group(2))
            ampm = 'AM' if m.group(3) == 'A' else 'PM'
            if hour == 12:
                hour24 = 0
            else:
                hour24 = hour
            if ampm == 'PM':
                hour24 += 12
            candidates.append((hour24, minute))

        # 5) Handle specific patterns like "12:00PM" (no space)
        for m in re.finditer(r'\b(\d{1,2}):(\d{2})([AP]M)\b', s):
            hour = int(m.group(1))
            minute = int(m.group(2))
            ampm = m.group(3)
            
            if ampm == 'AM' and hour == 12:
                hour24 = 0
            elif ampm == 'PM' and hour != 12:
                hour24 = hour + 12
            else:
                hour24 = hour
                
            candidates.append((hour24, minute))

        # 6) keywords
        if re.search(r'\bnoon\b', s, flags=re.IGNORECASE):
            candidates.append((12, 0))
        if re.search(r'\bmidnight\b', s, flags=re.IGNORECASE):
            candidates.append((0, 0))

        if not candidates:
            return ''

        # Prefer plausible local event times: 08:00–20:00
        def score(c):
            hour, minute = c
            # Base score favors daytime
            if 8 <= hour <= 20:
                return 3
            if 7 <= hour <= 21:
                return 2
            if 6 <= hour <= 22:
                return 1
            return 0

        # Pick highest score; if tie, first occurrence wins (already in order)
        best = max(candidates, key=score)
        h24, m = best

        # Format 12-hour canonical string
        ampm = 'AM'
        h12 = h24
        if h24 == 0:
            h12 = 12
            ampm = 'AM'
        elif 1 <= h24 < 12:
            ampm = 'AM'
        elif h24 == 12:
            h12 = 12
            ampm = 'PM'
        else:
            h12 = h24 - 12
            ampm = 'PM'

        return f"{h12}:{m:02d} {ampm}"
    
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
    
    def scrape_bu_hic_calendar(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Scrape BU HIC calendar - has structured event-list with event-date and event-time classes"""
        events = []
        
        # Find the event list container
        event_list = soup.find('div', class_='event-list')
        if not event_list:
            return events
        
        # Find all event dates (h3 with class event-date)
        event_dates = event_list.find_all('h3', class_='event-date')
        
        for date_header in event_dates:
            date_text = date_header.get_text().strip()
            # Parse date like "Wednesday, September 17"
            date_match = re.search(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\w+)\s+(\d{1,2})\b', date_text)
            
            if not date_match:
                continue
            
            day_name, month_name, day_num = date_match.groups()
            current_year = datetime.now().year
            
            try:
                date_obj = datetime.strptime(f"{month_name} {day_num} {current_year}", "%B %d %Y")
                if date_obj.date() < datetime.now().date():
                    date_obj = datetime.strptime(f"{month_name} {day_num} {current_year + 1}", "%B %d %Y")
                
                # Find the next ul element containing events for this date
                ul_element = date_header.find_next_sibling('ul')
                if ul_element:
                    # Find all li elements in this ul
                    event_items = ul_element.find_all('li')
                    
                    for li in event_items:
                        # Extract time
                        time_span = li.find('span', class_='event-time')
                        time_text = time_span.get_text().strip() if time_span else "TBD"
                        
                        # Extract title and link
                        link_span = li.find('span', class_='event-link')
                        if link_span:
                            link = link_span.find('a')
                            title = link.get_text().strip() if link else "Event"
                            event_url = link.get('href') if link else source_url
                            
                            # Make URL absolute
                            if event_url.startswith('/'):
                                from urllib.parse import urljoin
                                event_url = urljoin(source_url, event_url)
                        else:
                            title = "Event"
                            event_url = source_url
                        
                        # Extract description
                        desc_span = li.find('span', class_='event-desc')
                        description = desc_span.get_text().strip() if desc_span else ""
                        
                        event = {
                            'title': title,
                            'description': description,
                            'date': date_obj.strftime('%Y-%m-%d'),
                            'time': time_text,
                            'location': '',
                            'url': event_url,
                            'source_url': source_url,
                            'is_virtual': 'virtual' in description.lower() or 'zoom' in description.lower(),
                            'requires_registration': 'register' in description.lower() or 'rsvp' in description.lower(),
                            'categories': []
                        }
                        
                        events.append(event)
                        
            except ValueError:
                continue
        
        return events
    
    def scrape_mit_crib(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Scrape MIT CRIB - has table with meeting dates and speaker info"""
        events = []
        
        # Look for tables with meeting information
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # First cell contains date like "April 4"
                    date_cell = cells[0].get_text().strip()
                    date_match = re.search(r'\b(\w+)\s+(\d{1,2})\b', date_cell)
                    
                    if date_match:
                        month_name, day_num = date_match.groups()
                        current_year = datetime.now().year
                        
                        try:
                            date_obj = datetime.strptime(f"{month_name} {day_num} {current_year}", "%B %d %Y")
                            if date_obj.date() < datetime.now().date():
                                date_obj = datetime.strptime(f"{month_name} {day_num} {current_year + 1}", "%B %d %Y")
                            
                            # Second cell contains speaker and title info
                            speaker_cell = cells[1]
                            
                            # Extract speaker name
                            speaker_link = speaker_cell.find('a')
                            speaker_name = speaker_link.get_text().strip() if speaker_link else "TBD"
                            
                            # Extract speaker affiliation (in italics)
                            affiliation_elem = speaker_cell.find('i')
                            affiliation = affiliation_elem.get_text().strip() if affiliation_elem else ""
                            
                            # Extract title (usually in a separate p tag)
                            title_p = speaker_cell.find('p')
                            title = title_p.get_text().strip() if title_p else "CRIB Seminar"
                            
                            # Clean up title
                            if title and len(title) > 5:
                                title = title[:100] + "..." if len(title) > 100 else title
                            else:
                                title = f"CRIB Seminar: {speaker_name}"
                            
                            # Build description
                            description = f"Speaker: {speaker_name}"
                            if affiliation:
                                description += f" ({affiliation})"
                            if title and title != f"CRIB Seminar: {speaker_name}":
                                description += f"\nTitle: {title}"
                            
                            # Extract event URL if available
                            event_url = source_url
                            if speaker_link:
                                href = speaker_link.get('href')
                                if href:
                                    from urllib.parse import urljoin
                                    event_url = urljoin(source_url, href)
                            
                            event = {
                                'title': title,
                                'description': description,
                                'date': date_obj.strftime('%Y-%m-%d'),
                                'time': "12:00 PM",  # Default time from the page description
                                'location': 'Virtual via Zoom',
                                'url': event_url,
                                'source_url': source_url,
                                'is_virtual': True,
                                'requires_registration': False,
                                'categories': []
                            }
                            
                            events.append(event)
                        except ValueError:
                            continue
        
        return events
    
    def scrape_bu_csmet_seminar(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Scrape BU CSMET seminar series - has collapsible sections with event details"""
        events = []
        
        # Look for collapsible sections containing seminar information
        collapsible_sections = soup.find_all('div', class_='bu_collapsible_section')
        
        for section in collapsible_sections:
            # Look for the date/time pattern in the section
            section_text = section.get_text()
            
            # Look for pattern like "This Hybrid event will be held on Friday, 10th October 2025 at 10:00 am EST"
            date_match = re.search(r'\b(Friday|Monday|Tuesday|Wednesday|Thursday|Saturday|Sunday),?\s+\d{1,2}(st|nd|rd|th)?\s+(\w+)\s+(\d{4})\b', section_text)
            time_match = re.search(r'\b(\d{1,2}:\d{2})\s*(am|pm)\b', section_text)
            
            if date_match and time_match:
                day_name, _, month_name, year = date_match.groups()
                time_str, ampm = time_match.groups()
                
                # Extract title from the collapsible header
                collapsible_header = section.find_previous('h3', class_='bu_collapsible')
                title = collapsible_header.get_text().strip() if collapsible_header else "CSMET Seminar"
                
                # Extract speaker information
                speaker_info = ""
                speaker_link = section.find('a')
                if speaker_link:
                    speaker_info = speaker_link.get_text().strip()
                
                # Extract location information
                location = ""
                location_match = re.search(r'Room \d+,.*?(?:\n|$)', section_text)
                if location_match:
                    location = location_match.group(0).strip()
                
                # Build description
                description = section_text[:300] + "..." if len(section_text) > 300 else section_text
                
                try:
                    date_obj = datetime.strptime(f"{day_name} {month_name} {year}", "%A %B %Y")
                    
                    event = {
                        'title': title,
                        'description': description,
                        'date': date_obj.strftime('%Y-%m-%d'),
                        'time': f"{time_str} {ampm.upper()}",
                        'location': location,
                        'url': source_url,
                        'source_url': source_url,
                        'is_virtual': 'hybrid' in section_text.lower() or 'zoom' in section_text.lower(),
                        'requires_registration': False,
                        'categories': []
                    }
                    
                    events.append(event)
                except ValueError:
                    continue
        
        return events
    
    def scrape_brown_ccmb(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Scrape Brown CCMB events using the LiveWhale API"""
        events = []
        
        try:
            # Use the discovered API endpoint
            api_url = "https://events.brown.edu/live/calendar/view/all?user_tz=America%2FDetroit&template_vars=id,href,image_src,title,time,title_link,latitude,longitude,location,online_url,online_button_label,online_instructions,until,repeats,is_multi_day,is_first_multi_day,multi_day_span,tag_classes,category_classes,online_type,has_map,custom_ticket_required&syntax=%3Cwidget%20type%3D%22events_calendar%22%3E%3Carg%20id%3D%22mini_cal_heat_map%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22thumb_width%22%3E200%3C%2Farg%3E%3Carg%20id%3D%22thumb_height%22%3E200%3C%2Farg%3E%3Carg%20id%3D%22hide_repeats%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22show_groups%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22show_locations%22%3Efalse%3C%2Farg%3E%3Carg%20id%3D%22show_tags%22%3Efalse%3C%2Farg%3E%3Carg%20id%3D%22use_tag_classes%22%3Efalse%3C%2Farg%3E%3Carg%20id%3D%22search_all_events_only%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22use_modular_templates%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22display_all_day_events_last%22%3Etrue%3C%2Farg%3E%3Carg%20id%3D%22group%22%3EData%20Science%20Initiative%3C%2Farg%3E%3Carg%20id%3D%22group%22%3ECenter%20for%20Computational%20Molecular%20Biology%20%28CCMB%29%3C%2Farg%3E%3C%2Fwidget%3E"
            
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON response
            import json
            data = json.loads(response.text)
            
            # Extract events from the JSON structure
            events_data = data.get('events', {})
            
            for date_key, day_events in events_data.items():
                for event_data in day_events:
                    # Extract event information
                    title = event_data.get('title', '')
                    event_id = event_data.get('id', '')
                    
                    # Parse timestamp to get date and time
                    ts_start = event_data.get('ts_start', 0)
                    if ts_start:
                        from datetime import datetime
                        date_obj = datetime.fromtimestamp(ts_start)
                        date_str = date_obj.strftime('%Y-%m-%d')
                        time_str = date_obj.strftime('%I:%M %p').lstrip('0')
                    else:
                        date_str = date_key  # Fallback to date key
                        time_str = "TBD"
                    
                    # Extract location
                    location = event_data.get('location', '')
                    if location:
                        room = event_data.get('custom_room_number', '')
                        if room:
                            location = f"{location}, {room}"
                    
                    # Extract description from custom fields
                    description = event_data.get('custom_today_at_brown_message', '')
                    if not description:
                        description = event_data.get('title', '')
                    
                    # Clean up description HTML
                    if description:
                        from bs4 import BeautifulSoup
                        desc_soup = BeautifulSoup(description, 'html.parser')
                        description = desc_soup.get_text().strip()
                        if len(description) > 300:
                            description = description[:300] + "..."
                    
                    # Determine if virtual
                    is_virtual = event_data.get('is_online', '0') == '1'
                    online_url = event_data.get('online_url', '')
                    
                    # Build event URL
                    href = event_data.get('href', '')
                    event_url = f"https://events.brown.edu/{href}" if href else source_url
                    
                    # Extract categories
                    categories = event_data.get('categories', [])
                    tags = event_data.get('tags', [])
                    all_categories = categories + tags
                    
                    event = {
                        'title': title,
                        'description': description,
                        'date': date_str,
                        'time': time_str,
                        'location': location,
                        'url': event_url,
                        'source_url': source_url,
                        'is_virtual': is_virtual,
                        'requires_registration': False,  # Not specified in API
                        'categories': all_categories
                    }
                    
                    events.append(event)
            
        except Exception as e:
            self.logger.error(f"Error scraping Brown CCMB API: {e}")
        
        return events
    
    def scrape_mit_media_lab(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Scrape MIT Media Lab events"""
        events = []
        
        # Look for elements with date patterns
        date_elements = soup.find_all(string=re.compile(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'))
        
        for date_elem in date_elements:
            parent = date_elem.parent
            while parent and parent.name not in ['div', 'article', 'li', 'p']:
                parent = parent.parent
            
            if parent:
                full_text = parent.get_text()
                
                # Look for date pattern
                date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b', full_text)
                
                if date_match:
                    month_name, day_num, year = date_match.groups()
                    
                    # Extract title - look for text around the date
                    title = "MIT Media Lab Event"
                    
                    # Look for nearby text that could be a title
                    for sibling in parent.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b']):
                        sibling_text = sibling.get_text().strip()
                        if len(sibling_text) > 10 and len(sibling_text) < 100:
                            title = sibling_text
                            break
                    
                    try:
                        date_obj = datetime.strptime(f"{month_name} {day_num} {year}", "%b %d %Y")
                        
                        event = {
                            'title': title,
                            'description': full_text[:200] + "..." if len(full_text) > 200 else full_text,
                            'date': date_obj.strftime('%Y-%m-%d'),
                            'time': "TBD",  # Default time
                            'location': '',
                            'url': source_url,
                            'source_url': source_url,
                            'is_virtual': False,
                            'requires_registration': 'register' in full_text.lower(),
                            'categories': []
                        }
                        
                        events.append(event)
                    except ValueError:
                        continue
        
        return events
    
    def scrape_broad_institute(self, soup: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Scrape Broad Institute events - has JSON-LD structured data"""
        events = []
        
        # Look for JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Event':
                            event = self.extract_event_from_json_ld(item, source_url)
                            if event:
                                events.append(event)
            except:
                continue
        
        return events
    
    def extract_event_from_json_ld(self, data: dict, source_url: str) -> Dict[str, Any]:
        """Extract event from JSON-LD structured data"""
        
        try:
            title = data.get('name', 'Event')
            description = data.get('description', '')
            start_date = data.get('startDate', '')
            location = data.get('location', {})
            
            if isinstance(location, dict):
                location_name = location.get('name', '')
            else:
                location_name = str(location)
            
            # Parse date
            date_str = start_date
            time_str = "TBD"
            
            if 'T' in start_date:
                try:
                    date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y-%m-%d')
                    time_str = date_obj.strftime('%I:%M %p')
                except:
                    pass
            time_str = self.normalize_time_string(time_str)
            
            event = {
                'title': title,
                'description': description,
                'date': date_str,
                'time': time_str,
                'location': location_name,
                'url': source_url,
                'source_url': source_url,
                'is_virtual': 'virtual' in location_name.lower() or 'online' in description.lower(),
                'requires_registration': 'register' in description.lower() or 'rsvp' in description.lower(),
                'categories': []
            }
            
            return event
        except:
            return None 

    def is_placeholder_element(self, element) -> bool:
        """Detect navigation/search widgets that should not be treated as events."""
        if not element:
            return True
        
        tag_name = getattr(element, 'name', '').lower()
        if tag_name in {'nav', 'form', 'header', 'footer', 'aside'}:
            return True

        classes = []
        if element.has_attr('class'):
            classes = [cls.lower() for cls in element.get('class', [])]
        class_string = ' '.join(classes)
        placeholder_class_patterns = [
            'tribe-events-nav',
            'tribe-events-bar',
            'views-navigation',
            'events-search',
            'events-bar',
            'events-calendar-list',
            'calendar-nav',
            'calendar-pagination',
            'wp-block-calendar',
            'event-search',
            'event-filter'
        ]
        if any(pattern in class_string for pattern in placeholder_class_patterns):
            return True

        text = self.clean_text(element.get_text() or '').lower()
        placeholder_text_patterns = [
            'views navigation',
            'events search',
            'search events',
            'find events',
            'events navigation',
            'no events found',
            'thanksgiving day',
            'tbd',
            'to be determined'
        ]
        if text and len(text) < 80:
            if any(pattern in text for pattern in placeholder_text_patterns):
                return True
        if text and text in {'events', 'event', 'calendar', 'news & events'}:
            return True

        # Detect if element mainly contains form controls
        form_controls = element.find_all(['input', 'select', 'button'])
        if form_controls and len(form_controls) >= 2:
            return True

        return False

    def post_process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and enrich an event after initial extraction."""
        if not event:
            return None
        # Work on a shallow copy to avoid mutating the original reference
        processed = dict(event)
        try:
            processed = self.enrich_event_details(processed)
            processed = self.normalize_event_fields(processed)
        except Exception as e:
            self.logger.debug(f"Post-processing error for {processed.get('url', processed.get('source_url', 'unknown'))}: {e}")
        return processed

    def normalize_event_fields(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply consistent formatting and fallbacks to core event fields."""
        event['title'] = self.clean_text(event.get('title', ''))
        original_description = event.get('description', '')
        if self.is_generic_title(event['title']):
            title_from_desc = self.extract_title_from_description(original_description)
            if title_from_desc and not self.is_generic_title(title_from_desc):
                event['title'] = title_from_desc
        if self.is_generic_title(event['title']):
            title_from_url = self.derive_title_from_url(event.get('url') or event.get('source_url', ''))
            if title_from_url and not self.is_generic_title(title_from_url):
                event['title'] = title_from_url
        if self.is_generic_title(event['title']):
            fallback_description = self.clean_text(original_description)
            if fallback_description:
                event['title'] = fallback_description
        if self.is_generic_title(event['title']):
            domain_title = self.derive_title_from_domain(
                event.get('url') or event.get('source_url', ''),
                event.get('date', '')
            )
            if domain_title:
                event['title'] = domain_title
        raw_description = event.get('description', '')
        event['description'] = self.clean_text(raw_description, collapse_spaces=False)
        if len(event['description']) > 800:
            truncated = event['description'][:800].rsplit(' ', 1)[0]
            event['description'] = f"{truncated}..."
        if not event['description']:
            event['description'] = "Full details are available on the event page."

        event['time'] = self.normalize_time_string(event.get('time', ''))
        if not event['time']:
            event['time'] = 'Time TBD'

        event['location'] = self.clean_text(event.get('location', ''))
        event['url'] = event.get('url') or event.get('source_url', '')

        # Update virtual/registration flags using enriched description
        description_text = event.get('description', '')
        if description_text:
            event['is_virtual'] = event.get('is_virtual', False) or self.detect_virtual_event(description_text)
            event['requires_registration'] = event.get('requires_registration', False) or self.detect_registration_required(description_text)

        # Ensure categories is always a list
        categories = event.get('categories', [])
        if isinstance(categories, str):
            categories = [categories]
        event['categories'] = categories
        return event

    def enrich_event_details(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch event detail page when necessary to fill missing metadata."""
        if not self.needs_detail_enrichment(event):
            return event

        detail_url = event.get('url') or event.get('source_url')
        detail = self.fetch_detail_page(detail_url)
        if not detail:
            return event

        soup = detail['soup']
        text_content = detail['text']

        # Prefer structured data when present
        metadata = self.extract_event_metadata_from_jsonld(soup)
        if metadata:
            if self.is_generic_title(event.get('title', '')):
                meta_title = metadata.get('name') or metadata.get('headline')
                if meta_title and not self.is_generic_title(meta_title):
                    event['title'] = meta_title

            if self.is_time_missing(event.get('time', '')):
                start_value = metadata.get('startDate') or metadata.get('startTime')
                if start_value:
                    try:
                        dt = datetime.fromisoformat(start_value.replace('Z', '+00:00'))
                        event['time'] = dt.strftime('%I:%M %p')
                    except Exception:
                        pass

            if not event.get('description') or len(event['description'].strip()) < 40:
                meta_desc = metadata.get('description') or metadata.get('summary')
                if meta_desc:
                    event['description'] = meta_desc

            if not event.get('location'):
                location = metadata.get('location')
                if isinstance(location, dict):
                    event['location'] = location.get('name') or location.get('address', '')
                elif isinstance(location, str):
                    event['location'] = location

        detail_title = self.extract_title_from_detail(soup)
        if detail_title and not self.is_generic_title(detail_title):
            event['title'] = detail_title
        elif self.is_generic_title(event.get('title', '')):
            url_title = self.derive_title_from_url(event.get('url') or event.get('source_url', ''))
            if url_title and not self.is_generic_title(url_title):
                event['title'] = url_title
            else:
                desc_title = self.extract_title_from_description(event.get('description', ''))
                if desc_title and not self.is_generic_title(desc_title):
                    event['title'] = desc_title

        if not event.get('description') or len(event['description'].strip()) < 40:
            detail_description = self.extract_description_from_detail(soup)
            if not detail_description:
                detail_description = self.extract_description_from_text(text_content)
            if detail_description:
                event['description'] = detail_description

        if self.is_time_missing(event.get('time', '')):
            detail_time = self.extract_time_from_element(soup, soup) or self.extract_time_from_text(text_content)
            if detail_time:
                event['time'] = detail_time

        if not event.get('location'):
            detail_location = self.extract_location_from_detail(soup)
            if detail_location:
                event['location'] = detail_location

        # Re-evaluate flags with richer text
        if text_content:
            event['is_virtual'] = event.get('is_virtual', False) or self.detect_virtual_event(text_content)
            event['requires_registration'] = event.get('requires_registration', False) or self.detect_registration_required(text_content)

        return event

    def needs_detail_enrichment(self, event: Dict[str, Any]) -> bool:
        """Determine whether the event needs extra scraping."""
        title = event.get('title', '')
        description = event.get('description', '')
        time_value = event.get('time', '')

        has_generic_title = self.is_generic_title(title)
        description_short = len(description.strip()) < 40 or description.strip() == "Full details are available on the event page."
        missing_time = self.is_time_missing(time_value)
        url = event.get('url') or event.get('source_url')
        return bool(url and url.startswith('http') and (has_generic_title or description_short or missing_time))

    def is_time_missing(self, time_value: str) -> bool:
        if not time_value:
            return True
        lowered = time_value.strip().lower()
        if lowered in ('tbd', 'time tbd', 'tba', 'time tba', 'to be determined'):
            return True
        if lowered in ('', '00:00', '0:00', '12:00 am'):
            return True
        return False

    def fetch_detail_page(self, url: str) -> Dict[str, Any]:
        """Retrieve and cache the event detail page."""
        if not url or not url.startswith('http'):
            return None

        if url in self.detail_cache:
            return self.detail_cache[url]

        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            detail = {
                'soup': soup,
                'text': soup.get_text(separator=' ', strip=True)
            }
            self.detail_cache[url] = detail
            return detail
        except Exception as e:
            self.logger.debug(f"Failed to fetch detail page {url}: {e}")
            self.detail_cache[url] = None
            return None

    def extract_event_metadata_from_jsonld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Return first Event object from JSON-LD if available."""
        if not soup:
            return None
        for script in soup.find_all('script', type='application/ld+json'):
            raw = script.string
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if not isinstance(obj, dict):
                    continue
                if obj.get('@type') == 'Event':
                    return obj
                # Handle graph collections
                graph = obj.get('@graph')
                if isinstance(graph, list):
                    for item in graph:
                        if isinstance(item, dict) and item.get('@type') == 'Event':
                            return item
        return None

    def extract_title_from_detail(self, soup: BeautifulSoup) -> str:
        """Extract a descriptive title from the detail page."""
        if not soup:
            return ''
        meta_selectors = [
            ('property', 'og:title'),
            ('name', 'twitter:title')
        ]
        for attr, value in meta_selectors:
            tag = soup.find('meta', attrs={attr: value})
            if tag and tag.get('content'):
                title = self.clean_text(tag['content'])
                if title:
                    return title

        header = soup.find(['h1', 'h2'])
        if header:
            title = self.clean_text(header.get_text())
            if title:
                return title

        if soup.title and soup.title.string:
            title = self.clean_text(soup.title.string)
            if title:
                return title

        return ''

    def extract_description_from_detail(self, soup: BeautifulSoup) -> str:
        """Extract a meaningful description from the detail page."""
        if not soup:
            return ''
        meta_selectors = [
            ('property', 'og:description'),
            ('name', 'description'),
            ('name', 'twitter:description')
        ]
        for attr, value in meta_selectors:
            tag = soup.find('meta', attrs={attr: value})
            if tag and tag.get('content'):
                description = self.clean_text(tag['content'], collapse_spaces=False)
                if description:
                    return description

        article = soup.find('article')
        if article:
            paragraphs = article.find_all(['p', 'div'])
            texts = [self.clean_text(p.get_text(), collapse_spaces=False) for p in paragraphs if self.clean_text(p.get_text())]
            combined = ' '.join(t for t in texts if t)
            if combined:
                return combined

        paragraphs = soup.find_all('p')
        collected = []
        for paragraph in paragraphs:
            text = self.clean_text(paragraph.get_text(), collapse_spaces=False)
            if len(text) >= 40:
                collected.append(text)
            if len(' '.join(collected)) > 320:
                break
        if collected:
            return ' '.join(collected)

        return ''

    def extract_description_from_text(self, text: str) -> str:
        """Fallback description extraction using raw text."""
        if not text:
            return ''
        sentences = re.split(r'(?<=[.!?])\s+', text)
        collected = []
        for sentence in sentences:
            cleaned = self.clean_text(sentence)
            if len(cleaned) >= 40:
                collected.append(cleaned)
            if len(' '.join(collected)) >= 280:
                break
        return ' '.join(collected)

    def extract_location_from_detail(self, soup: BeautifulSoup) -> str:
        """Extract location information from the detail page."""
        if not soup:
            return ''
        meta_location = soup.find('meta', attrs={'property': 'event:location'})
        if meta_location and meta_location.get('content'):
            return self.clean_text(meta_location.get('content'))

        location = self.extract_location(soup)
        if location:
            return self.clean_text(location)

        # Look for address microdata
        address = soup.find(attrs={'itemprop': 'location'})
        if address:
            return self.clean_text(address.get_text())

        return ''

    def normalize_time_string(self, time_str: str) -> str:
        """Normalize different time formats into a canonical 12-hour format."""
        if not time_str:
            return ''
        t = time_str.strip()
        if not t:
            return ''

        lowered = t.lower()
        if any(keyword in lowered for keyword in ['tbd', 'to be determined', 'tba']):
            return 'Time TBD'
        if 'all day' in lowered:
            return 'All Day'

        # Handle "1pm", "1 pm", "1:30 pm"
        match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$', lowered)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or '0')
            ampm = match.group(3).upper()
            if hour == 0:
                hour = 12
                ampm = 'AM'
            elif hour > 12:
                hour = hour - 12
            return f"{hour}:{minute:02d} {ampm}"

        # Handle "13:00" 24-hour format
        match = re.match(r'^(\d{1,2}):(\d{2})$', lowered)
        if match:
            hour24 = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour24 <= 23:
                if hour24 == 0:
                    return f"12:{minute:02d} AM"
                if hour24 == 12:
                    return f"12:{minute:02d} PM"
                if hour24 > 12:
                    return f"{hour24 - 12}:{minute:02d} PM"
                return f"{hour24}:{minute:02d} AM"

        # Handle compact "12:00pm" format
        match = re.match(r'^(\d{1,2}):(\d{2})(am|pm)$', lowered)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(3).upper()
            if hour == 0:
                hour = 12
                ampm = 'AM'
            elif hour > 12:
                hour -= 12
            return f"{hour}:{minute:02d} {ampm}"

        # As a fallback, reuse text time extraction
        extracted = self.extract_time_from_text(t)
        if extracted:
            return extracted

        return t

    def clean_text(self, text: str, collapse_spaces: bool = True) -> str:
        """Normalize whitespace and strip surrounding spaces."""
        if not text:
            return ''
        if collapse_spaces:
            return re.sub(r'\s+', ' ', text).strip()

        # Keep intentional paragraph breaks while normalizing spacing
        normalized = text.replace('\r\n', '\n')
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)
        normalized = re.sub(r'[ \t]+', ' ', normalized)
        lines = [line.strip() for line in normalized.split('\n')]
        return '\n'.join([line for line in lines if line]).strip()

    def is_generic_title(self, title: str) -> bool:
        """Identify placeholder or non-descriptive titles."""
        if not title:
            return True
        cleaned = self.clean_text(title).lower()
        generic_titles = {
            'event',
            'events',
            'calendar of events',
            'calendar',
            'upcoming events',
            'view event',
            'event details',
            'learn more',
            'read more',
            'news & events',
            'views navigation',
            'events search',
            'thanksgiving day',
            'tbd',
            'to be determined',
            'ai + biology event',
            'ai + biology events',
            'mit ai + biology event',
            'mit ai + biology events'
        }
        if cleaned in generic_titles:
            return True
        generic_prefixes = [
            'ai + biology event',
            'ai + biology events',
            'mit ai + biology event',
            'mit ai + biology events',
            'bu ai + biology event',
            'bu ai + biology events'
        ]
        if any(cleaned.startswith(prefix) for prefix in generic_prefixes):
            return True
        return False

    def extract_title_from_description(self, description: str) -> str:
        """Try to derive a meaningful title from the description text."""
        if not description:
            return ''
        sentences = re.split(r'(?<=[.!?])\s+', description.strip())
        for sentence in sentences:
            candidate = self.clean_text(sentence)
            if 10 < len(candidate) <= 140 and not self.is_generic_title(candidate):
                return candidate
        return ''

    def derive_title_from_url(self, url: str) -> str:
        """Construct a title candidate from the event URL path."""
        if not url:
            return ''
        try:
            parsed = urlparse(url)
        except Exception:
            return ''
        segments = [seg for seg in parsed.path.split('/') if seg]
        for segment in reversed(segments):
            if segment.isdigit():
                continue
            cleaned = re.sub(r'[-_]+', ' ', segment)
            cleaned = re.sub(r'\.[a-z0-9]+$', '', cleaned, flags=re.IGNORECASE)
            cleaned = self.clean_text(cleaned)
            if not cleaned or len(cleaned) < 3:
                continue
            candidate = cleaned.title()
            if not self.is_generic_title(candidate):
                return candidate
        return ''

    def derive_title_from_domain(self, url: str, date_str: str) -> str:
        """Fallback title combining source domain/path and event date."""
        if not url:
            return ''
        try:
            parsed = urlparse(url)
        except Exception:
            return ''

        host = parsed.hostname or ''
        host_parts = [part for part in host.split('.') if part and part not in {'www', 'com', 'org', 'net', 'edu'}]

        path_parts = [seg for seg in parsed.path.split('/') if seg]
        filtered_path = []
        skip_tokens = {'events', 'event', 'calendar', 'calendars', 'calendar_event', 'view', 'views', 'news'}
        for seg in path_parts:
            if seg.lower() in skip_tokens:
                continue
            filtered_path.append(seg)

        components = host_parts[:2]
        if filtered_path:
            components.append(filtered_path[0])

        if not components:
            components = [host or 'Event']

        base = ' '.join(self.clean_text(comp).title() for comp in components if comp)
        if not base:
            base = 'Event'

        title = f"{base} Calendar"
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                title = f"{title} ({date_obj.strftime('%b %d, %Y')})"
            except ValueError:
                pass

        if self.is_generic_title(title):
            return ''
        return title

    def refresh_event_metadata(
        self,
        days_ahead: int = 180,
        include_past: bool = False,
        lookback_days: int = 365,
        max_events: int = 200
    ) -> int:
        """Re-process stored events that are missing key metadata."""
        events = self.db.get_events(
            days_ahead=days_ahead,
            include_past=include_past,
            lookback_days=lookback_days,
            limit=5000 if not max_events else max(max_events * 2, 1000)
        )
        updated = 0
        processed = 0

        for event in events:
            if max_events and processed >= max_events:
                break

            if not self.needs_detail_enrichment(event):
                continue

            enriched = self.post_process_event(event)
            if not enriched:
                continue

            processed += 1
            if self.event_metadata_changed(event, enriched):
                enriched['id'] = event['id']
                self.db.update_event_metadata(enriched)
                updated += 1

        if updated:
            self.logger.info(f"Enriched metadata for {updated} stored events")
        return updated

    def event_metadata_changed(self, original: Dict[str, Any], enriched: Dict[str, Any]) -> bool:
        """Check if enrichment materially updated the event."""
        text_fields = ['title', 'description', 'time', 'location', 'url']
        for field in text_fields:
            orig_value = self.clean_text(str(original.get(field, '')))
            new_value = self.clean_text(str(enriched.get(field, '')))
            if orig_value != new_value:
                return True

        bool_fields = ['is_virtual', 'requires_registration']
        for field in bool_fields:
            if bool(original.get(field, False)) != bool(enriched.get(field, False)):
                return True

        return False