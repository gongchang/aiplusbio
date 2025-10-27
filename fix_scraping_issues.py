#!/usr/bin/env python3
"""
Fix scraping issues:
1. Improve event extraction for problematic sites
2. Better URL extraction to get specific event pages
3. Better title extraction to avoid generic titles
"""

import sqlite3
import re

def clean_up_bad_events():
    """Remove events with generic titles and bad URLs"""
    
    print("🧹 Cleaning up bad events...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Find events with generic titles or bad URLs
    cursor.execute('''
        SELECT id, title, url, source_url 
        FROM events 
        WHERE title IN ('Events', 'Calendar of Events', 'Event', 'Calendar')
        OR url = source_url
        OR title LIKE '%Events%' AND LENGTH(title) < 20
    ''')
    
    bad_events = cursor.fetchall()
    print(f"🔍 Found {len(bad_events)} events with generic titles or bad URLs")
    
    for event_id, title, url, source_url in bad_events:
        print(f"   Removing: {title} (URL: {url})")
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Removed {len(bad_events)} bad events")

def update_event_extraction():
    """Update event scraper with better extraction logic"""
    
    print("🔧 Updating event extraction logic...")
    
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Add better event extraction method
    better_extraction = '''
    def extract_events_with_better_logic(self, soup, source_url):
        """Extract events with improved logic for problematic sites"""
        events = []
        
        # Look for events in different ways
        selectors = [
            'article', '.event', '.events', '.event-item', '.calendar-event',
            '.seminar', '.lecture', '.talk', '.workshop', '.meeting',
            'li', '.item', '.entry', '.post', '.content-item'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                event = self.extract_event_from_element(element, source_url)
                if event and self.is_valid_event(event):
                    events.append(event)
        
        # If no events found with selectors, try broader approach
        if not events:
            # Look for any element with date-like content
            date_patterns = [
                r'\\b\\d{1,2}/\\d{1,2}/\\d{4}\\b',
                r'\\b\\d{4}-\\d{2}-\\d{2}\\b',
                r'\\b(January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+\\d{4}\\b'
            ]
            
            for pattern in date_patterns:
                elements_with_dates = soup.find_all(text=re.compile(pattern, re.IGNORECASE))
                for text_element in elements_with_dates:
                    parent = text_element.parent
                    if parent:
                        event = self.extract_event_from_element(parent, source_url)
                        if event and self.is_valid_event(event):
                            events.append(event)
        
        return events
    
    def is_valid_event(self, event):
        """Check if event is valid (not generic)"""
        if not event:
            return False
        
        title = event.get('title', '').strip()
        
        # Reject generic titles
        generic_titles = ['events', 'event', 'calendar', 'calendar of events', 'upcoming events']
        if title.lower() in generic_titles or len(title) < 10:
            return False
        
        # Must have a date
        if not event.get('date'):
            return False
        
        # Must have a title
        if not title:
            return False
        
        return True
    
    def extract_better_event_url(self, element, source_url, title):
        """Extract better event URLs that point to specific event pages"""
        
        # Look for links that might be event-specific
        links = element.find_all('a', href=True)
        
        best_url = source_url  # Default fallback
        best_score = 0
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            # Skip if it's the same as source URL
            if href == source_url or href == source_url.rstrip('/'):
                continue
            
            # Skip obvious non-event links
            skip_patterns = ['mailto:', 'tel:', 'javascript:', '#', 'map', 'directions', 'contact', 'subscribe']
            if any(pattern in href.lower() for pattern in skip_patterns):
                continue
            
            score = 0
            
            # Score based on link text relevance
            if title and any(word.lower() in link_text.lower() for word in title.split()[:3]):
                score += 10
            
            # Score based on URL patterns
            event_patterns = ['event', 'seminar', 'lecture', 'talk', 'workshop', 'meeting']
            if any(pattern in href.lower() for pattern in event_patterns):
                score += 5
            
            # Score based on URL structure (prefer specific pages)
            if '/event/' in href or '/events/' in href or '/seminar/' in href:
                score += 8
            
            # Prefer relative URLs that can be made absolute
            if href.startswith('/'):
                score += 3
            
            # Prefer URLs with more path segments (more specific)
            path_segments = href.split('/')
            score += len([s for s in path_segments if s]) * 2
            
            if score > best_score:
                best_score = score
                best_url = href
        
        # Make relative URLs absolute
        if best_url.startswith('/'):
            from urllib.parse import urljoin
            best_url = urljoin(source_url, best_url)
        elif not best_url.startswith('http'):
            from urllib.parse import urljoin
            best_url = urljoin(source_url, best_url)
        
        return best_url
'''
    
    # Add the new methods before the existing extract_events method
    if 'def extract_events_with_better_logic(' not in content:
        # Find a good place to insert (before extract_events method)
        extract_pos = content.find('def extract_events(')
        if extract_pos != -1:
            content = content[:extract_pos] + better_extraction + '\n    ' + content[extract_pos:]
            print("✅ Added better event extraction methods")
    
    # Update the extract_events method to use the new logic
    old_extract_events = '''    def extract_events(self, soup, source_url):
        """Extract events from a BeautifulSoup object"""
        events = []
        
        # Look for events in different ways
        selectors = [
            'article', '.event', '.events', '.event-item', '.calendar-event',
            '.seminar', '.lecture', '.talk', '.workshop', '.meeting',
            'li', '.item', '.entry', '.post', '.content-item'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                event = self.extract_event_from_element(element, source_url)
                if event:
                    events.append(event)
        
        return events'''
    
    new_extract_events = '''    def extract_events(self, soup, source_url):
        """Extract events from a BeautifulSoup object with improved logic"""
        return self.extract_events_with_better_logic(soup, source_url)'''
    
    if old_extract_events in content:
        content = content.replace(old_extract_events, new_extract_events)
        print("✅ Updated extract_events method to use better logic")
    
    # Update extract_event_from_element to use better URL extraction
    old_url_extraction = '''        # Extract URL
        url = self.extract_best_event_url(element, source_url, title)'''
    
    new_url_extraction = '''        # Extract URL with better logic
        url = self.extract_better_event_url(element, source_url, title)'''
    
    if old_url_extraction in content:
        content = content.replace(old_url_extraction, new_url_extraction)
        print("✅ Updated URL extraction to use better logic")
    
    with open('event_scraper.py', 'w') as f:
        f.write(content)

def main():
    print("🔧 Fixing Scraping Issues...")
    print("=" * 40)
    
    clean_up_bad_events()
    update_event_extraction()
    
    print("\n🎉 Scraping issues fixed!")
    print("💡 Improvements:")
    print("   - Removed events with generic titles")
    print("   - Better event extraction for problematic sites")
    print("   - Improved URL extraction for specific event pages")
    print("   - Better validation of event data")
    print("\n🚀 Restart server to apply changes")

if __name__ == '__main__':
    main()
