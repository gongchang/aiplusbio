#!/usr/bin/env python3
"""
Investigate sites that should have events but aren't being found
"""

import requests
from bs4 import BeautifulSoup
import time

def test_site_accessibility():
    """Test if sites are accessible and have content"""
    
    sites_to_test = [
        "https://www.ericandwendyschmidtcenter.org/events#upcoming-events",
        "https://be.mit.edu/our-community/seminars/",
        "https://events.seas.harvard.edu/",
        "https://wi.mit.edu/events"
    ]
    
    print("🔍 Testing Site Accessibility...")
    print("=" * 50)
    
    for site in sites_to_test:
        print(f"\n🌐 Testing: {site}")
        
        try:
            # Test with different user agents
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(site, headers=headers, timeout=15, verify=False)
            
            print(f"   Status: {response.status_code}")
            print(f"   Content Length: {len(response.text)} characters")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for common event indicators
                event_indicators = [
                    'event', 'seminar', 'workshop', 'lecture', 'talk', 
                    'conference', 'meeting', 'calendar', 'schedule'
                ]
                
                found_indicators = []
                for indicator in event_indicators:
                    if indicator in response.text.lower():
                        found_indicators.append(indicator)
                
                print(f"   Event Indicators Found: {found_indicators[:5]}")
                
                # Look for date patterns
                import re
                date_patterns = [
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
                    r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
                ]
                
                dates_found = []
                for pattern in date_patterns:
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    dates_found.extend(matches[:3])  # Limit to first 3
                
                print(f"   Date Patterns Found: {dates_found[:3]}")
                
                # Check for links that might be events
                links = soup.find_all('a', href=True)
                event_links = [link for link in links if any(indicator in link.get('href', '').lower() for indicator in event_indicators)]
                print(f"   Potential Event Links: {len(event_links)}")
                
            else:
                print(f"   ❌ Failed to access site")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}...")
        
        time.sleep(2)  # Be respectful

if __name__ == '__main__':
    test_site_accessibility()
