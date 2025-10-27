#!/usr/bin/env python3
"""
Final sophisticated scraper for IAIFI with proper HTML structure handling
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime
import sqlite3

class FinalIAIFIScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_iaifi_events(self):
        """Scrape IAIFI events with sophisticated structure handling"""
        print("🔍 Scraping IAIFI events (sophisticated structure handling)...")
        
        url = "https://iaifi.org/events.html"
        
        try:
            response = self.session.get(url, verify=False, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Find all list items that contain event information
            all_list_items = soup.find_all('li')
            
            print(f"✅ Found {len(all_list_items)} total list items")
            
            # Process each list item
            for item in all_list_items:
                event = self.extract_event_from_list_item(item, url)
                if event:
                    events.append(event)
                    print(f"✅ Extracted event: {event['title'][:50]}...")
            
            # Remove duplicates based on title and date
            unique_events = []
            seen = set()
            
            for event in events:
                key = (event['title'], event['date'])
                if key not in seen:
                    seen.add(key)
                    unique_events.append(event)
            
            print(f"✅ Found {len(unique_events)} unique events from IAIFI")
            return unique_events
            
        except Exception as e:
            print(f"❌ Error scraping IAIFI: {e}")
            return []
    
    def extract_event_from_list_item(self, item, base_url):
        """Extract event information from a list item"""
        try:
            # Get all text content
            text_content = item.get_text(strip=True)
            
            # Skip empty or very short content
            if len(text_content) < 30:
                return None
            
            # Extract date first
            date = self.extract_date(text_content)
            if not date:
                return None
            
            # Extract speaker name (usually in bold)
            speaker = self.extract_speaker(item)
            
            # Extract title
            title = self.extract_title(item, text_content, speaker)
            if not title:
                return None
            
            # Extract time and location
            time_location = self.extract_time_location(text_content)
            
            # Create final title
            if time_location and title:
                final_title = f"{title} ({time_location})"
            else:
                final_title = title
            
            # Extract URL
            link = item.find('a', href=True)
            event_url = urljoin(base_url, link['href']) if link else base_url
            
            return {
                'title': final_title,
                'date': date,
                'url': event_url,
                'description': "",
                'source_url': base_url
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting from list item: {e}")
            return None
    
    def extract_date(self, text):
        """Extract date from text"""
        date_patterns = [
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group()
        
        return None
    
    def extract_speaker(self, item):
        """Extract speaker name from bold elements"""
        bold_elements = item.find_all(['strong', 'b'])
        if bold_elements:
            speaker = bold_elements[0].get_text(strip=True)
            # Remove date from speaker name
            speaker = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', speaker, flags=re.I).strip()
            if speaker and speaker.lower() not in ['speaker to be announced', 'title to come']:
                return speaker
        return None
    
    def extract_title(self, item, text_content, speaker):
        """Extract title from item"""
        # If we have a speaker, use it as title
        if speaker:
            return speaker
        
        # Remove date from text
        clean_text = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', text_content, flags=re.I)
        clean_text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', clean_text, flags=re.I)
        
        # Take the first meaningful line
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        for line in lines:
            if line and len(line) > 10 and line.lower() not in ['speaker to be announced', 'title to come', 'abstract to come']:
                return line
        
        return None
    
    def extract_time_location(self, text):
        """Extract time and location from text"""
        time_location = ""
        
        # Extract time
        time_pattern = r'\d{1,2}:\d{2}(?:am|pm)–\d{1,2}:\d{2}(?:am|pm)'
        time_match = re.search(time_pattern, text, re.I)
        if time_match:
            time_location = time_match.group()
        
        # Extract location
        location_pattern = r'(?:MIT|Harvard|Room|Building|Hall|Center)[^,]*'
        location_match = re.search(location_pattern, text, re.I)
        if location_match:
            location = location_match.group()
            if time_location:
                time_location += ", " + location
            else:
                time_location = location
        
        return time_location
    
    def add_events_to_database(self, events):
        """Add events to the database"""
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        added_count = 0
        
        for event in events:
            try:
                # Check if event already exists
                cursor.execute("""
                    SELECT id FROM events 
                    WHERE title = ? AND date = ? AND source_url = ?
                """, (event['title'], event['date'], event['source_url']))
                
                if cursor.fetchone() is None:
                    # Add new event
                    cursor.execute("""
                        INSERT INTO events (title, description, date, time, location, url, source_url, is_virtual, requires_registration, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event['title'],
                        event['description'],
                        event['date'],
                        '',  # time
                        '',  # location
                        event['url'],
                        event['source_url'],
                        False,  # is_virtual
                        False,  # requires_registration
                        datetime.now()
                    ))
                    added_count += 1
                    
            except Exception as e:
                print(f"Error adding event {event['title']}: {e}")
        
        conn.commit()
        conn.close()
        
        return added_count

def main():
    """Test the final IAIFI scraper"""
    print("🚀 Testing Final IAIFI Scraper")
    print("=" * 50)
    
    scraper = FinalIAIFIScraper()
    
    # Test IAIFI
    events = scraper.scrape_iaifi_events()
    
    if events:
        print(f"💾 Adding {len(events)} events to database...")
        added_count = scraper.add_events_to_database(events)
        print(f"✅ Added {added_count} new events to database")
        
        # Show some examples
        print("\n📋 Sample events:")
        for event in events[:5]:
            print(f"  • {event['title']} ({event['date']})")
    else:
        print("❌ No events found")

if __name__ == "__main__":
    main()










