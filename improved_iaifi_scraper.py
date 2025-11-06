#!/usr/bin/env python3
"""
Improved scraper for IAIFI with better bullet-point structure handling
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime
import sqlite3

class ImprovedIAIFIScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_iaifi_events(self):
        """Scrape IAIFI events with improved bullet-point structure handling"""
        print("🔍 Scraping IAIFI events (improved bullet-point structure)...")
        
        url = "https://iaifi.org/events.html"
        
        try:
            response = self.session.get(url, verify=False, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Find the "Upcoming Colloquia" section specifically
            upcoming_section = None
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            for heading in headings:
                heading_text = heading.get_text(strip=True).lower()
                if 'upcoming colloquia' in heading_text:
                    upcoming_section = heading
                    break
            
            if not upcoming_section:
                print("❌ Could not find 'Upcoming Colloquia' section")
                return []
            
            print("✅ Found 'Upcoming Colloquia' section")
            
            # Get all list items under this section
            current = upcoming_section.find_next_sibling()
            event_items = []
            
            while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if current.name == 'ul':
                    list_items = current.find_all('li')
                    event_items.extend(list_items)
                elif current.name == 'li':
                    event_items.append(current)
                
                current = current.find_next_sibling()
            
            print(f"✅ Found {len(event_items)} list items")
            
            # Process each list item as a complete event
            for item in event_items:
                event = self.extract_complete_event_from_item(item, url)
                if event:
                    events.append(event)
                    print(f"✅ Extracted complete event: {event['title'][:60]}...")
            
            print(f"✅ Found {len(events)} events from IAIFI")
            return events
            
        except Exception as e:
            print(f"❌ Error scraping IAIFI: {e}")
            return []
    
    def extract_complete_event_from_item(self, item, base_url):
        """Extract complete event information from a list item"""
        try:
            # Get all text content from the item
            text_content = item.get_text(strip=True)
            
            # Skip empty or very short content
            if len(text_content) < 20:
                return None
            
            # Extract speaker name (usually in bold)
            speaker = None
            bold_elements = item.find_all(['strong', 'b'])
            if bold_elements:
                speaker = bold_elements[0].get_text(strip=True)
            
            # Extract date using multiple patterns
            date = None
            date_patterns = [
                r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{4}-\d{2}-\d{2}\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.I)
                if match:
                    date = match.group()
                    break
            
            if not date:
                return None
            
            # Extract title
            title = None
            
            # If we have a speaker, use it as the title
            if speaker:
                # Remove date from speaker name
                clean_speaker = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', speaker, flags=re.I).strip()
                if clean_speaker and clean_speaker.lower() not in ['speaker to be announced', 'title to come']:
                    title = clean_speaker
            
            # If no title from speaker, try to extract from text
            if not title:
                # Remove date from text
                clean_text = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', text_content, flags=re.I)
                clean_text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', clean_text, flags=re.I)
                
                # Take the first meaningful line
                lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
                for line in lines:
                    if line and len(line) > 10 and line.lower() not in ['speaker to be announced', 'title to come', 'abstract to come']:
                        title = line
                        break
            
            if not title:
                return None
            
            # Extract time and location
            time_location = ""
            time_pattern = r'\d{1,2}:\d{2}(?:am|pm)–\d{1,2}:\d{2}(?:am|pm)'
            time_match = re.search(time_pattern, text_content, re.I)
            if time_match:
                time_location = time_match.group()
            
            # Look for location (usually after time)
            location_pattern = r'(?:MIT|Harvard|Room|Building|Hall|Center)[^,]*'
            location_match = re.search(location_pattern, text_content, re.I)
            if location_match:
                if time_location:
                    time_location += ", " + location_match.group()
                else:
                    time_location = location_match.group()
            
            # Extract URL
            link = item.find('a', href=True)
            event_url = urljoin(base_url, link['href']) if link else base_url
            
            # Create a more descriptive title if we have time/location info
            if time_location and title:
                full_title = f"{title} ({time_location})"
            else:
                full_title = title
            
            return {
                'title': full_title,
                'date': date,
                'url': event_url,
                'description': "",
                'source_url': base_url
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting from item: {e}")
            return None
    
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
    """Test the improved IAIFI scraper"""
    print("🚀 Testing Improved IAIFI Scraper")
    print("=" * 50)
    
    scraper = ImprovedIAIFIScraper()
    
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











