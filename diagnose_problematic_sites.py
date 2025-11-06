#!/usr/bin/env python3
"""
Diagnose why specific sites aren't finding events
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

def test_site_content(url, site_name):
    """Test a site and analyze its content structure"""
    print(f"\n🔍 Testing {site_name}")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to access site")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for common event indicators
        event_indicators = [
            'event', 'events', 'seminar', 'seminars', 'workshop', 'workshops',
            'lecture', 'lectures', 'talk', 'talks', 'calendar', 'schedule'
        ]
        
        # Check for event-related elements
        event_elements = []
        for indicator in event_indicators:
            elements = soup.find_all(text=re.compile(indicator, re.I))
            event_elements.extend(elements)
        
        print(f"📊 Found {len(event_elements)} event-related text elements")
        
        # Look for date patterns
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'  # DD Month YYYY
        ]
        
        date_matches = []
        for pattern in date_patterns:
            matches = re.findall(pattern, response.text, re.I)
            date_matches.extend(matches)
        
        print(f"📅 Found {len(date_matches)} date patterns")
        if date_matches:
            print(f"   Sample dates: {date_matches[:5]}")
        
        # Look for links that might be events
        links = soup.find_all('a', href=True)
        event_links = []
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if link text or URL contains event indicators
            if any(indicator in text.lower() or indicator in href.lower() for indicator in event_indicators):
                event_links.append((text, href))
        
        print(f"🔗 Found {len(event_links)} potential event links")
        if event_links:
            print("   Sample event links:")
            for text, href in event_links[:5]:
                print(f"     '{text}' -> {href}")
        
        # Check for specific HTML structures
        structures = {
            'div with event class': len(soup.find_all('div', class_=re.compile('event', re.I))),
            'article tags': len(soup.find_all('article')),
            'li with event class': len(soup.find_all('li', class_=re.compile('event', re.I))),
            'h2/h3 tags': len(soup.find_all(['h2', 'h3'])),
            'calendar elements': len(soup.find_all(class_=re.compile('calendar', re.I)))
        }
        
        print(f"🏗️  HTML Structure Analysis:")
        for structure, count in structures.items():
            print(f"   {structure}: {count}")
        
        # Check for JavaScript content
        scripts = soup.find_all('script')
        js_content = ' '.join([script.get_text() for script in scripts])
        
        if 'event' in js_content.lower() or 'calendar' in js_content.lower():
            print("⚠️  Site appears to use JavaScript for event loading")
        
        # Check for iframes
        iframes = soup.find_all('iframe')
        if iframes:
            print(f"⚠️  Site contains {len(iframes)} iframes (may load content dynamically)")
        
        print(f"✅ Site analysis complete")
        
    except Exception as e:
        print(f"❌ Error analyzing site: {e}")

def main():
    """Main diagnostic function"""
    print("🔍 Diagnosing Problematic Sites")
    print("=" * 60)
    
    sites_to_test = [
        ("https://www.ericandwendyschmidtcenter.org/events#upcoming-events", "Eric & Wendy Schmidt Center"),
        ("https://be.mit.edu/our-community/seminars/", "BE MIT Seminars"),
        ("https://events.seas.harvard.edu/", "SEAS Harvard Events"),
        ("https://wi.mit.edu/events", "WI MIT Events")
    ]
    
    for url, name in sites_to_test:
        test_site_content(url, name)
        time.sleep(2)  # Be nice to servers
    
    print(f"\n🎯 Summary:")
    print("=" * 60)
    print("This analysis will help identify why these sites aren't finding events.")
    print("Common issues:")
    print("- JavaScript-rendered content")
    print("- Different HTML structure")
    print("- Events in iframes")
    print("- Different date/time formats")
    print("- Events require authentication")
    print("- Events are in RSS feeds instead of HTML")

if __name__ == "__main__":
    main()











