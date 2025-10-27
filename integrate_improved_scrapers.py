#!/usr/bin/env python3
"""
Integrate improved scrapers into the main system
"""

import sqlite3
from datetime import datetime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

def scrape_seas_harvard():
    """Scrape SEAS Harvard Events"""
    url = "https://events.seas.harvard.edu/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = []
        
        # Look for event containers
        event_containers = soup.find_all('div', class_=re.compile('event', re.I))
        
        for container in event_containers:
            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4']) or container.find('a')
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                continue
                
            # Extract date
            date_text = container.get_text()
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', date_text)
            if not date_match:
                date_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', date_text, re.I)
            
            if date_match:
                date = date_match.group()
            else:
                continue
                
            # Extract URL
            link = container.find('a', href=True)
            if link:
                event_url = urljoin(url, link['href'])
            else:
                event_url = url
                
            events.append({
                'title': title,
                'date': date,
                'url': event_url,
                'description': "",
                'source_url': url
            })
        
        return events
        
    except Exception as e:
        print(f"❌ Error scraping SEAS Harvard: {e}")
        return []

def scrape_wi_mit_events():
    """Scrape WI MIT Events"""
    url = "https://wi.mit.edu/events"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = []
        
        # Look for article tags
        articles = soup.find_all('article')
        
        for article in articles:
            # Extract title
            title_elem = article.find(['h1', 'h2', 'h3', 'h4']) or article.find('a')
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                continue
                
            # Extract date
            date_text = article.get_text()
            date_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', date_text, re.I)
            if date_match:
                date = date_match.group()
            else:
                continue
                
            # Extract URL
            link = article.find('a', href=True)
            if link:
                event_url = urljoin(url, link['href'])
            else:
                event_url = url
                
            events.append({
                'title': title,
                'date': date,
                'url': event_url,
                'description': "",
                'source_url': url
            })
        
        return events
        
    except Exception as e:
        print(f"❌ Error scraping WI MIT: {e}")
        return []

def add_events_to_database(events):
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
    """Test and integrate the improved scrapers"""
    print("🔧 Integrating Improved Scrapers")
    print("=" * 50)
    
    all_events = []
    
    # Test SEAS Harvard
    print("🔍 Testing SEAS Harvard scraper...")
    seas_events = scrape_seas_harvard()
    print(f"✅ Found {len(seas_events)} events from SEAS Harvard")
    all_events.extend(seas_events)
    
    # Test WI MIT
    print("🔍 Testing WI MIT scraper...")
    wi_events = scrape_wi_mit_events()
    print(f"✅ Found {len(wi_events)} events from WI MIT")
    all_events.extend(wi_events)
    
    print(f"\n📊 Total events found: {len(all_events)}")
    
    if all_events:
        print("💾 Adding events to database...")
        added_count = add_events_to_database(all_events)
        print(f"✅ Added {added_count} new events to database")
        
        # Show some examples
        print("\n📋 Sample events:")
        for event in all_events[:3]:
            print(f"  • {event['title']} ({event['date']})")
    else:
        print("❌ No events found to add")

if __name__ == "__main__":
    main()
