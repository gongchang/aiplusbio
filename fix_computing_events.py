#!/usr/bin/env python3
"""
Script to fix issues with computing events:
1. Remove events with generic titles like "Event", "TBA", etc.
2. Remove events with broken or generic URLs
3. Fix date parsing issues
4. Validate URLs and remove non-existent events
"""

import sqlite3
import requests
from datetime import datetime
from urllib.parse import urlparse
import re


class ComputingEventsFixer:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def get_bad_events(self):
        """Get events that need fixing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get events with generic titles
        generic_titles = [
            'Event', 'TBA', 'Events Search and Views Navigation',
            'Upcoming Developer Events & Conferences', 'Events'
        ]
        
        generic_title_condition = " OR ".join([f"title = '{title}'" for title in generic_titles])
        
        cursor.execute(f'''
            SELECT id, title, url, date, source_url 
            FROM computing_events 
            WHERE {generic_title_condition}
            OR title LIKE '%Navigation%'
            OR title LIKE '%Search%'
            OR url LIKE '%/events/%'
            OR url LIKE '%/events'
            OR url = source_url
            ORDER BY date
        ''')
        
        bad_events = cursor.fetchall()
        conn.close()
        return bad_events
    
    def test_url(self, url):
        """Test if a URL is accessible and contains valid content"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            # Check if response is successful
            if response.status_code not in [200, 301, 302]:
                return False, f"HTTP {response.status_code}"
            
            # Check if content looks like an event page
            content = response.text.lower()
            
            # Generic pages that don't contain specific events
            generic_indicators = [
                'event listings', 'upcoming events', 'all events',
                'search events', 'filter events', 'event calendar',
                'no events found', 'coming soon'
            ]
            
            if any(indicator in content for indicator in generic_indicators):
                return False, "Generic event listing page"
            
            # Check for event-specific content
            event_indicators = [
                'register', 'registration', 'ticket', 'schedule',
                'speaker', 'agenda', 'venue', 'location'
            ]
            
            if any(indicator in content for indicator in event_indicators):
                return True, "Valid event page"
            
            # If it's a short page, it's probably not a real event
            if len(response.text) < 5000:
                return False, "Page too short for event content"
            
            return True, "Appears to be valid"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def is_generic_title(self, title):
        """Check if title is generic and not meaningful"""
        generic_patterns = [
            r'^Event$',
            r'^TBA$',
            r'.*Navigation.*',
            r'.*Search.*',
            r'^Events$',
            r'.*Upcoming.*Events.*',
            r'^.*Event.*$'  # Very generic pattern
        ]
        
        title_lower = title.lower()
        for pattern in generic_patterns:
            if re.match(pattern, title_lower):
                return True
        
        # Check if title is too short or too generic
        if len(title.strip()) < 5:
            return True
        
        # Check for common generic words
        generic_words = ['event', 'events', 'seminar', 'colloquium', 'meeting']
        if title_lower in generic_words:
            return True
        
        return False
    
    def is_generic_url(self, url, source_url):
        """Check if URL is generic (points to listing pages rather than specific events)"""
        url_lower = url.lower()
        
        # Same as source URL (not specific event)
        if url == source_url:
            return True
        
        # Generic URL patterns
        generic_patterns = [
            '/events/',
            '/events',
            '/calendar/',
            '/calendar',
            '/upcoming-events',
            '/all-events',
            '/event-listings',
            '/search',
            '/filter'
        ]
        
        for pattern in generic_patterns:
            if pattern in url_lower:
                return True
        
        # Check if URL doesn't have event-specific identifiers
        # Good URLs usually have event IDs, names, or dates
        if not any(char.isdigit() for char in url) and len(url.split('/')) < 5:
            return True
        
        return False
    
    def fix_events(self):
        """Fix the computing events database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔍 Analyzing computing events...")
        
        # Get all computing events
        cursor.execute('SELECT id, title, url, date, source_url FROM computing_events ORDER BY date')
        all_events = cursor.fetchall()
        
        print(f"📊 Total computing events: {len(all_events)}")
        
        events_to_delete = []
        events_to_update = []
        
        for event_id, title, url, date, source_url in all_events:
            issues = []
            
            # Check for generic titles
            if self.is_generic_title(title):
                issues.append("Generic title")
            
            # Check for generic URLs
            if self.is_generic_url(url, source_url):
                issues.append("Generic URL")
            
            # Test URL accessibility
            if not issues:  # Only test if no other issues
                is_valid, reason = self.test_url(url)
                if not is_valid:
                    issues.append(f"Invalid URL: {reason}")
            
            if issues:
                print(f"❌ Event {event_id}: {title}")
                print(f"   Issues: {', '.join(issues)}")
                print(f"   URL: {url}")
                events_to_delete.append(event_id)
            else:
                print(f"✅ Event {event_id}: {title}")
        
        # Delete problematic events
        if events_to_delete:
            print(f"\n🗑️  Deleting {len(events_to_delete)} problematic events...")
            placeholders = ','.join(['?' for _ in events_to_delete])
            cursor.execute(f'DELETE FROM computing_events WHERE id IN ({placeholders})', events_to_delete)
            deleted_count = cursor.rowcount
            print(f"✅ Deleted {deleted_count} events")
        
        # Update any events that need date fixes
        print(f"\n📅 Checking date formats...")
        cursor.execute('SELECT id, title, date FROM computing_events WHERE date NOT LIKE "%-%-%"')
        bad_dates = cursor.fetchall()
        
        for event_id, title, date in bad_dates:
            print(f"⚠️  Event {event_id}: Bad date format '{date}' - {title}")
            # Update with current date as fallback
            cursor.execute('UPDATE computing_events SET date = ? WHERE id = ?', 
                         (datetime.now().strftime('%Y-%m-%d'), event_id))
        
        if bad_dates:
            print(f"✅ Fixed {len(bad_dates)} date format issues")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Computing events cleanup completed!")
        
        # Show final stats
        self.show_stats()
    
    def show_stats(self):
        """Show final statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM computing_events')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM computing_events WHERE date >= date("now")')
        future_events = cursor.fetchone()[0]
        
        print(f"\n📈 Final Statistics:")
        print(f"   Total computing events: {total_events}")
        print(f"   Future events: {future_events}")
        
        # Show sample of remaining events
        cursor.execute('SELECT title, url, date FROM computing_events WHERE date >= date("now") ORDER BY date LIMIT 10')
        remaining_events = cursor.fetchall()
        
        print(f"\n📋 Sample of remaining events:")
        for i, (title, url, date) in enumerate(remaining_events, 1):
            print(f"   {i}. {title} ({date})")
            print(f"      {url}")
        
        conn.close()


def main():
    """Main function"""
    print("🔧 Computing Events Fixer")
    print("=" * 50)
    
    fixer = ComputingEventsFixer()
    fixer.fix_events()


if __name__ == "__main__":
    main()



