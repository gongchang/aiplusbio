#!/usr/bin/env python3
"""
Advanced scraper with multiple techniques for problematic sites
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json
import time
from datetime import datetime
import sqlite3

class AdvancedSiteScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_eric_schmidt_center_advanced(self):
        """Advanced scraping for Eric & Wendy Schmidt Center"""
        print("🔍 Advanced scraping: Eric & Wendy Schmidt Center...")
        
        url = "https://www.ericandwendyschmidtcenter.org/events#upcoming-events"
        
        try:
            response = self.session.get(url, verify=False, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Method 1: Look for specific event containers
            event_containers = soup.find_all('div', class_=re.compile('event', re.I))
            print(f"Found {len(event_containers)} event containers")
            
            for container in event_containers:
                # Extract all text and look for date patterns
                container_text = container.get_text()
                
                # Look for various date formats
                date_patterns = [
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    r'\b\d{4}-\d{2}-\d{2}\b'
                ]
                
                date_found = None
                for pattern in date_patterns:
                    match = re.search(pattern, container_text, re.I)
                    if match:
                        date_found = match.group()
                        break
                
                if not date_found:
                    continue
                
                # Extract title from various elements
                title = None
                title_elements = [
                    container.find('h1'), container.find('h2'), container.find('h3'),
                    container.find('h4'), container.find('h5'), container.find('h6'),
                    container.find('a'), container.find('strong'), container.find('b')
                ]
                
                for elem in title_elements:
                    if elem and elem.get_text(strip=True):
                        potential_title = elem.get_text(strip=True)
                        # Skip generic titles
                        if potential_title.lower() not in ['events', 'event', 'upcoming events', 'past events', 'read more']:
                            title = potential_title
                            break
                
                if not title:
                    # Try to extract from the first meaningful text
                    lines = [line.strip() for line in container_text.split('\n') if line.strip()]
                    for line in lines:
                        if line and line.lower() not in ['events', 'event', 'upcoming events', 'past events', 'read more']:
                            # Remove date from title
                            clean_title = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', line, flags=re.I).strip()
                            if clean_title and len(clean_title) > 5:
                                title = clean_title
                                break
                
                if title:
                    # Extract URL
                    link = container.find('a', href=True)
                    event_url = urljoin(url, link['href']) if link else url
                    
                    events.append({
                        'title': title,
                        'date': date_found,
                        'url': event_url,
                        'description': "",
                        'source_url': url
                    })
            
            # Method 2: Look for JSON-LD structured data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Event':
                        title = data.get('name', '')
                        date = data.get('startDate', '')
                        if title and date:
                            events.append({
                                'title': title,
                                'date': date,
                                'url': data.get('url', url),
                                'description': data.get('description', ''),
                                'source_url': url
                            })
                except:
                    continue
            
            print(f"✅ Found {len(events)} events from Eric & Wendy Schmidt Center")
            return events
            
        except Exception as e:
            print(f"❌ Error scraping Eric & Wendy Schmidt Center: {e}")
            return []
    
    def scrape_be_mit_seminars_advanced(self):
        """Advanced scraping for BE MIT Seminars"""
        print("🔍 Advanced scraping: BE MIT Seminars...")
        
        url = "https://be.mit.edu/our-community/seminars/"
        
        try:
            response = self.session.get(url, verify=False, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Method 1: Look for seminar entries in headings
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                
                # Look for date patterns
                date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', heading_text)
                if date_match:
                    date = date_match.group()
                    
                    # Extract title (remove date)
                    title = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', heading_text).strip()
                    if title and title.lower() not in ['seminars', 'events', 'seminar']:
                        events.append({
                            'title': title,
                            'date': date,
                            'url': url,
                            'description': "",
                            'source_url': url
                        })
            
            # Method 2: Look for seminar containers
            seminar_containers = soup.find_all('div', class_=re.compile('seminar', re.I))
            
            for container in seminar_containers:
                container_text = container.get_text()
                
                # Look for date
                date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', container_text)
                if date_match:
                    date = date_match.group()
                    
                    # Extract title from container
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'strong'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and title.lower() not in ['seminars', 'events', 'seminar']:
                            events.append({
                                'title': title,
                                'date': date,
                                'url': url,
                                'description': "",
                                'source_url': url
                            })
            
            # Method 3: Look for any text with dates and seminar-like content
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if len(line) > 20:  # Meaningful line
                    date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', line)
                    if date_match:
                        date = date_match.group()
                        
                        # Extract title (remove date and common words)
                        title = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', line).strip()
                        title = re.sub(r'\b(seminar|event|talk|lecture)\b', '', title, flags=re.I).strip()
                        
                        if title and len(title) > 10 and title.lower() not in ['seminars', 'events']:
                            events.append({
                                'title': title,
                                'date': date,
                                'url': url,
                                'description': "",
                                'source_url': url
                            })
            
            print(f"✅ Found {len(events)} events from BE MIT Seminars")
            return events
            
        except Exception as e:
            print(f"❌ Error scraping BE MIT Seminars: {e}")
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
    """Test advanced scraping techniques"""
    print("🚀 Testing Advanced Scraping Techniques")
    print("=" * 50)
    
    scraper = AdvancedSiteScraper()
    
    all_events = []
    
    # Test Eric & Wendy Schmidt Center
    eric_events = scraper.scrape_eric_schmidt_center_advanced()
    all_events.extend(eric_events)
    
    # Test BE MIT Seminars
    be_events = scraper.scrape_be_mit_seminars_advanced()
    all_events.extend(be_events)
    
    print(f"\n📊 Total events found: {len(all_events)}")
    
    if all_events:
        print("💾 Adding events to database...")
        added_count = scraper.add_events_to_database(all_events)
        print(f"✅ Added {added_count} new events to database")
        
        # Show some examples
        print("\n📋 Sample events:")
        for event in all_events[:5]:
            print(f"  • {event['title']} ({event['date']})")
    else:
        print("❌ No events found")

if __name__ == "__main__":
    main()











