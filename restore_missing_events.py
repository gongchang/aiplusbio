#!/usr/bin/env python3
"""
Script to restore missing legitimate events that were incorrectly deleted.
This script will re-scrape the sources to restore good events.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
from urllib.parse import urljoin, urlparse
from database import Database


class MissingEventsRestorer:
    def __init__(self, db_path='events.db'):
        self.db = Database(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def is_legitimate_event(self, title, url, source_url):
        """Check if an event is legitimate and should be restored"""
        if not title or not title.strip():
            return False
        
        title = title.strip()
        
        # Skip obviously generic titles
        generic_titles = ['Event', 'Events', 'TBA', 'TBD', 'Navigation', 'Search']
        if title in generic_titles:
            return False
        
        # Skip date-only titles
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', title) or re.match(r'^\w+\s+\d{1,2},\s+\d{4}$', title):
            return False
        
        # Skip titles that are too short
        if len(title) < 10:
            return False
        
        # Skip if URL is the same as source (generic listing page)
        if url == source_url:
            return False
        
        # Skip generic URL patterns
        generic_patterns = ['/events/', '/events', '/calendar/', '/calendar', '/search', '/filter']
        for pattern in generic_patterns:
            if url.endswith(pattern):
                return False
        
        return True
    
    def scrape_bu_hic_events(self):
        """Scrape BU HIC events"""
        print("🔍 Scraping BU HIC events...")
        
        url = "https://www.bu.edu/hic/noteworthy/calendar/"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            
            # Look for event links
            event_links = soup.find_all('a', href=True)
            
            for link in event_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not title or len(title) < 10:
                    continue
                
                # Skip generic links
                if title.lower() in ['calendar', 'events', 'more', 'read more']:
                    continue
                
                full_url = urljoin(url, href)
                
                if self.is_legitimate_event(title, full_url, url):
                    # Try to extract date from nearby elements
                    date = self.extract_date_from_context(link)
                    
                    event = {
                        'title': title,
                        'description': '',
                        'date': date or datetime.now().strftime('%Y-%m-%d'),
                        'time': '',
                        'location': '',
                        'url': full_url,
                        'source_url': url,
                        'is_virtual': False,
                        'requires_registration': False,
                        'categories': []
                    }
                    events.append(event)
            
            return events
            
        except Exception as e:
            print(f"Error scraping BU HIC: {e}")
            return []
    
    def scrape_mit_biology_events(self):
        """Scrape MIT Biology events"""
        print("🔍 Scraping MIT Biology events...")
        
        url = "https://biology.mit.edu/events/"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            
            # Look for event elements
            event_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'event|item', re.I))
            
            for element in event_elements:
                # Extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                
                # Extract URL
                link = element.find('a', href=True)
                if link:
                    event_url = urljoin(url, link.get('href'))
                else:
                    event_url = url
                
                if self.is_legitimate_event(title, event_url, url):
                    # Try to extract date
                    date = self.extract_date_from_text(element.get_text())
                    
                    event = {
                        'title': title,
                        'description': '',
                        'date': date or datetime.now().strftime('%Y-%m-%d'),
                        'time': '',
                        'location': '',
                        'url': event_url,
                        'source_url': url,
                        'is_virtual': False,
                        'requires_registration': False,
                        'categories': []
                    }
                    events.append(event)
            
            return events
            
        except Exception as e:
            print(f"Error scraping MIT Biology: {e}")
            return []
    
    def scrape_bcs_events(self):
        """Scrape MIT BCS events"""
        print("🔍 Scraping MIT BCS events...")
        
        url = "https://bcs.mit.edu/events"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            
            # Look for event elements
            event_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'event|item', re.I))
            
            for element in event_elements:
                # Extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                
                # Extract URL
                link = element.find('a', href=True)
                if link:
                    event_url = urljoin(url, link.get('href'))
                else:
                    event_url = url
                
                if self.is_legitimate_event(title, event_url, url):
                    # Try to extract date
                    date = self.extract_date_from_text(element.get_text())
                    
                    event = {
                        'title': title,
                        'description': '',
                        'date': date or datetime.now().strftime('%Y-%m-%d'),
                        'time': '',
                        'location': '',
                        'url': event_url,
                        'source_url': url,
                        'is_virtual': False,
                        'requires_registration': False,
                        'categories': []
                    }
                    events.append(event)
            
            return events
            
        except Exception as e:
            print(f"Error scraping MIT BCS: {e}")
            return []
    
    def extract_date_from_text(self, text):
        """Extract date from text"""
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if pattern == r'(\d{1,2})/(\d{1,2})/(\d{4})':
                        month, day, year = match.groups()
                        date_str = f"{month}/{day}/{year}"
                        parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                    elif pattern == r'(\d{4})-(\d{2})-(\d{2})':
                        year, month, day = match.groups()
                        date_str = f"{year}-{month}-{day}"
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                    elif pattern == r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})':
                        month_name, day, year = match.groups()
                        date_str = f"{month_name} {day} {year}"
                        parsed_date = datetime.strptime(date_str, '%B %d %Y')
                    elif pattern == r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})':
                        month_name, day, year = match.groups()
                        date_str = f"{month_name} {day} {year}"
                        parsed_date = datetime.strptime(date_str, '%b %d %Y')
                    
                    # Only return future dates
                    if parsed_date.date() >= datetime.now().date():
                        return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def extract_date_from_context(self, element):
        """Extract date from context around an element"""
        # Look in parent elements for date information
        current = element.parent
        for _ in range(3):  # Check up to 3 parent levels
            if current:
                date = self.extract_date_from_text(current.get_text())
                if date:
                    return date
                current = current.parent
        return None
    
    def restore_events(self):
        """Restore missing events from various sources"""
        print("🔄 Restoring missing events...")
        
        all_events = []
        
        # Scrape from various sources
        all_events.extend(self.scrape_bu_hic_events())
        all_events.extend(self.scrape_mit_biology_events())
        all_events.extend(self.scrape_bcs_events())
        
        print(f"📊 Found {len(all_events)} potential events to restore")
        
        # Add events to database
        restored_count = 0
        for event in all_events:
            try:
                # Check if event already exists
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id FROM events 
                    WHERE title = ? AND url = ?
                ''', (event['title'], event['url']))
                
                if not cursor.fetchone():
                    event_id = self.db.add_event(event)
                    if event_id:
                        restored_count += 1
                        print(f"✅ Restored: {event['title']}")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ Error restoring {event['title']}: {e}")
        
        print(f"\n🎉 Restored {restored_count} events!")
        
        # Show final stats
        self.show_stats()
    
    def show_stats(self):
        """Show final statistics"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM events')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM events WHERE date >= date("now")')
        future_events = cursor.fetchone()[0]
        
        print(f"\n📈 Final Statistics:")
        print(f"   Total events: {total_events}")
        print(f"   Future events: {future_events}")
        
        # Show events by source
        cursor.execute('SELECT source_url, COUNT(*) FROM events GROUP BY source_url ORDER BY COUNT(*) DESC')
        source_counts = cursor.fetchall()
        
        print(f"\n📊 Events by Source:")
        for source, count in source_counts:
            print(f"   {source}: {count} events")
        
        conn.close()


def main():
    """Main function"""
    print("🔄 Missing Events Restorer")
    print("=" * 50)
    
    restorer = MissingEventsRestorer()
    restorer.restore_events()


if __name__ == "__main__":
    main()



