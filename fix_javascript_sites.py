#!/usr/bin/env python3
"""
Fix JavaScript-rendered sites by adding specific scraping logic
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json
import time

def scrape_eric_schmidt_center():
    """Scrape Eric & Wendy Schmidt Center events"""
    print("🔍 Scraping Eric & Wendy Schmidt Center...")
    
    url = "https://www.ericandwendyschmidtcenter.org/events#upcoming-events"
    
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
                
            # Extract description
            desc_elem = container.find(['p', 'div'], class_=re.compile('desc|summary', re.I))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            events.append({
                'title': title,
                'date': date,
                'url': event_url,
                'description': description,
                'source_url': url
            })
        
        print(f"✅ Found {len(events)} events from Eric & Wendy Schmidt Center")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping Eric & Wendy Schmidt Center: {e}")
        return []

def scrape_be_mit_seminars():
    """Scrape BE MIT Seminars"""
    print("🔍 Scraping BE MIT Seminars...")
    
    url = "https://be.mit.edu/our-community/seminars/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = []
        
        # Look for seminar entries in headings
        headings = soup.find_all(['h2', 'h3', 'h4'])
        
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            
            # Look for date patterns in heading or nearby text
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', heading_text)
            if not date_match:
                # Check next sibling for date
                next_elem = heading.find_next_sibling()
                if next_elem:
                    date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', next_elem.get_text())
            
            if date_match:
                date = date_match.group()
                
                # Extract title (remove date from heading)
                title = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', heading_text).strip()
                if title:
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

def scrape_seas_harvard():
    """Scrape SEAS Harvard Events"""
    print("🔍 Scraping SEAS Harvard Events...")
    
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
        
        print(f"✅ Found {len(events)} events from SEAS Harvard")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping SEAS Harvard: {e}")
        return []

def scrape_wi_mit_events():
    """Scrape WI MIT Events"""
    print("🔍 Scraping WI MIT Events...")
    
    url = "https://wi.mit.edu/events"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = []
        
        # Look for article tags (found 37 in diagnostic)
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
        
        print(f"✅ Found {len(events)} events from WI MIT")
        return events
        
    except Exception as e:
        print(f"❌ Error scraping WI MIT: {e}")
        return []

def main():
    """Test the improved scraping for problematic sites"""
    print("🔧 Testing Improved Scraping for JavaScript Sites")
    print("=" * 60)
    
    all_events = []
    
    # Test each site
    all_events.extend(scrape_eric_schmidt_center())
    all_events.extend(scrape_be_mit_seminars())
    all_events.extend(scrape_seas_harvard())
    all_events.extend(scrape_wi_mit_events())
    
    print(f"\n📊 Summary:")
    print("=" * 60)
    print(f"Total events found: {len(all_events)}")
    
    for event in all_events[:5]:  # Show first 5 events
        print(f"  • {event['title']} ({event['date']}) - {event['source_url']}")
    
    if all_events:
        print(f"\n✅ Successfully found events from problematic sites!")
        print("Next step: Integrate these functions into the main scraper")
    else:
        print(f"\n❌ Still no events found. May need JavaScript rendering.")

if __name__ == "__main__":
    main()











