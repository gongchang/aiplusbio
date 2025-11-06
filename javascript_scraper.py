#!/usr/bin/env python3
"""
JavaScript-enabled scraper using Selenium for problematic sites
"""

import time
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

class JavaScriptScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with fallback options"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to setup ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("✅ Selenium WebDriver setup successful")
            except Exception as e:
                print(f"⚠️  ChromeDriver setup failed: {e}")
                print("Falling back to requests-based scraping")
                self.driver = None
                
        except ImportError:
            print("⚠️  Selenium not available, using requests-based scraping")
            self.driver = None
    
    def get_page_content(self, url, wait_time=3):
        """Get page content with JavaScript rendering if available"""
        if self.driver:
            try:
                print(f"🌐 Loading {url} with JavaScript rendering...")
                self.driver.get(url)
                time.sleep(wait_time)  # Wait for JavaScript to load
                
                # Scroll to load more content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                page_source = self.driver.page_source
                return BeautifulSoup(page_source, 'html.parser')
                
            except Exception as e:
                print(f"❌ JavaScript rendering failed: {e}")
                return self.fallback_request(url)
        else:
            return self.fallback_request(url)
    
    def fallback_request(self, url):
        """Fallback to regular requests"""
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"❌ Fallback request failed: {e}")
            return None
    
    def scrape_eric_schmidt_center(self):
        """Scrape Eric & Wendy Schmidt Center with JavaScript"""
        print("🔍 Scraping Eric & Wendy Schmidt Center (JavaScript)...")
        
        url = "https://www.ericandwendyschmidtcenter.org/events#upcoming-events"
        soup = self.get_page_content(url, wait_time=5)
        
        if not soup:
            return []
        
        events = []
        
        # Look for event containers with more specific selectors
        event_selectors = [
            'div[class*="event"]',
            'div[class*="Event"]',
            'article',
            '.event-item',
            '.event-card',
            '[data-event]'
        ]
        
        for selector in event_selectors:
            containers = soup.select(selector)
            if containers:
                print(f"✅ Found {len(containers)} containers with selector: {selector}")
                break
        
        if not containers:
            # Fallback: look for any div with event-related text
            containers = soup.find_all('div')
            containers = [c for c in containers if 'event' in c.get_text().lower()]
        
        for container in containers:
            # Extract title
            title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5']) or container.find('a')
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                continue
            
            # Skip generic titles
            if title.lower() in ['events', 'event', 'upcoming events', 'past events']:
                continue
                
            # Extract date
            date_text = container.get_text()
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
        
        print(f"✅ Found {len(events)} events from Eric & Wendy Schmidt Center")
        return events
    
    def scrape_be_mit_seminars(self):
        """Scrape BE MIT Seminars with JavaScript"""
        print("🔍 Scraping BE MIT Seminars (JavaScript)...")
        
        url = "https://be.mit.edu/our-community/seminars/"
        soup = self.get_page_content(url, wait_time=5)
        
        if not soup:
            return []
        
        events = []
        
        # Look for seminar entries
        seminar_selectors = [
            'div[class*="seminar"]',
            'div[class*="event"]',
            'article',
            '.seminar-item',
            '.event-item'
        ]
        
        for selector in seminar_selectors:
            containers = soup.select(selector)
            if containers:
                print(f"✅ Found {len(containers)} containers with selector: {selector}")
                break
        
        if not containers:
            # Fallback: look for headings with dates
            containers = soup.find_all(['h2', 'h3', 'h4', 'h5'])
        
        for container in containers:
            container_text = container.get_text(strip=True)
            
            # Look for date patterns
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', container_text)
            if not date_match:
                # Check next sibling for date
                next_elem = container.find_next_sibling()
                if next_elem:
                    date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', next_elem.get_text())
            
            if date_match:
                date = date_match.group()
                
                # Extract title (remove date from heading)
                title = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', container_text).strip()
                if title and title.lower() not in ['seminars', 'events']:
                    events.append({
                        'title': title,
                        'date': date,
                        'url': url,
                        'description': "",
                        'source_url': url
                    })
        
        print(f"✅ Found {len(events)} events from BE MIT Seminars")
        return events
    
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
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()

def main():
    """Test JavaScript-enabled scraping"""
    print("🚀 Testing JavaScript-Enabled Scraping")
    print("=" * 50)
    
    scraper = JavaScriptScraper()
    
    try:
        all_events = []
        
        # Test Eric & Wendy Schmidt Center
        eric_events = scraper.scrape_eric_schmidt_center()
        all_events.extend(eric_events)
        
        # Test BE MIT Seminars
        be_events = scraper.scrape_be_mit_seminars()
        all_events.extend(be_events)
        
        print(f"\n📊 Total events found: {len(all_events)}")
        
        if all_events:
            print("💾 Adding events to database...")
            added_count = scraper.add_events_to_database(all_events)
            print(f"✅ Added {added_count} new events to database")
            
            # Show some examples
            print("\n📋 Sample events:")
            for event in all_events[:3]:
                print(f"  • {event['title']} ({event['date']})")
        else:
            print("❌ No events found")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    main()











