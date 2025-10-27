#!/usr/bin/env python3
"""
Specialized scraper for IAIFI and other sites with bullet-point event structures
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime
import sqlite3

class BulletPointEventScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_iaifi_events(self):
        """Scrape IAIFI events with bullet-point structure"""
        print("🔍 Scraping IAIFI events (bullet-point structure)...")
        
        url = "https://iaifi.org/events.html"
        
        try:
            response = self.session.get(url, verify=False, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Find all sections that might contain events
            event_sections = []
            
            # Look for sections with "Upcoming" in the heading
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text(strip=True).lower()
                if any(keyword in heading_text for keyword in ['upcoming', 'events', 'colloquia', 'seminars', 'talks']):
                    event_sections.append(heading)
            
            print(f"✅ Found {len(event_sections)} potential event sections")
            
            for section in event_sections:
                # Get the next sibling elements that might contain bullet points
                current = section.find_next_sibling()
                
                while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Look for bullet points (li elements) or paragraphs with bullet-like content
                    if current.name == 'ul':
                        list_items = current.find_all('li')
                        for item in list_items:
                            event = self.extract_event_from_bullet_point(item, url)
                            if event:
                                events.append(event)
                                print(f"✅ Extracted bullet-point event: {event['title'][:50]}...")
                    
                    elif current.name == 'li':
                        event = self.extract_event_from_bullet_point(current, url)
                        if event:
                            events.append(event)
                            print(f"✅ Extracted bullet-point event: {event['title'][:50]}...")
                    
                    elif current.name == 'p':
                        # Check if paragraph contains bullet-like content
                        text = current.get_text(strip=True)
                        if text.startswith('•') or text.startswith('*') or text.startswith('-'):
                            event = self.extract_event_from_text(text, url)
                            if event:
                                events.append(event)
                                print(f"✅ Extracted text event: {event['title'][:50]}...")
                    
                    current = current.find_next_sibling()
            
            # Fallback: Look for any content with dates
            if not events:
                print("🔍 Fallback: Looking for date patterns in all text...")
                events = self.extract_events_by_date_patterns(soup, url)
            
            print(f"✅ Found {len(events)} events from IAIFI")
            return events
            
        except Exception as e:
            print(f"❌ Error scraping IAIFI: {e}")
            return []
    
    def extract_event_from_bullet_point(self, element, base_url):
        """Extract event information from a bullet point element"""
        try:
            text_content = element.get_text(strip=True)
            
            # Skip empty or very short content
            if len(text_content) < 20:
                return None
            
            # Extract speaker name (usually in bold or first part)
            speaker = None
            bold_elements = element.find_all(['strong', 'b'])
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
            
            # If we have a speaker, use it as part of the title
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
            
            # Extract URL
            link = element.find('a', href=True)
            event_url = urljoin(base_url, link['href']) if link else base_url
            
            return {
                'title': title,
                'date': date,
                'url': event_url,
                'description': "",
                'source_url': base_url
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting from bullet point: {e}")
            return None
    
    def extract_event_from_text(self, text, base_url):
        """Extract event from text content"""
        try:
            # Remove bullet point markers
            text = re.sub(r'^[•*\-]\s*', '', text)
            
            # Extract date
            date = None
            date_patterns = [
                r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    date = match.group()
                    break
            
            if not date:
                return None
            
            # Extract title (remove date)
            title = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', text, flags=re.I).strip()
            title = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', title, flags=re.I).strip()
            
            if not title or len(title) < 5:
                return None
            
            return {
                'title': title,
                'date': date,
                'url': base_url,
                'description': "",
                'source_url': base_url
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting from text: {e}")
            return None
    
    def extract_events_by_date_patterns(self, soup, base_url):
        """Fallback: Extract events by looking for date patterns in all text"""
        events = []
        
        try:
            # Get all text content
            text_content = soup.get_text()
            
            # Split into lines and look for patterns
            lines = text_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Look for lines with dates and speaker information
                date_match = re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', line, re.I)
                
                if date_match and len(line) > 30:
                    date = date_match.group()
                    
                    # Extract title (remove date and common words)
                    title = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', line, flags=re.I).strip()
                    title = re.sub(r'\b(speaker to be announced|title to come|abstract to come)\b', '', title, flags=re.I).strip()
                    
                    if title and len(title) > 10:
                        events.append({
                            'title': title,
                            'date': date,
                            'url': base_url,
                            'description': "",
                            'source_url': base_url
                        })
            
            print(f"✅ Extracted {len(events)} events by date patterns")
            return events
            
        except Exception as e:
            print(f"❌ Date pattern extraction failed: {e}")
            return []
    
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
    """Test the bullet-point event scraper"""
    print("🚀 Testing Bullet-Point Event Scraper")
    print("=" * 50)
    
    scraper = BulletPointEventScraper()
    
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










