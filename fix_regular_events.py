#!/usr/bin/env python3
"""
Script to fix issues with regular events:
1. Remove events with generic titles like "Event", "TBA", etc.
2. Remove events with broken or generic URLs
3. Remove duplicate events
4. Fix date parsing issues
"""

import sqlite3
import requests
from datetime import datetime
from urllib.parse import urlparse
import re


class RegularEventsFixer:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def get_problematic_events(self):
        """Get events that need fixing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get events with generic titles or problematic patterns
        cursor.execute('''
            SELECT id, title, url, date, source_url 
            FROM events 
            WHERE title IN ('Event', 'TBA', 'Events Search and Views Navigation')
            OR title LIKE '%Navigation%'
            OR title LIKE '%Search%'
            OR url LIKE '%/events/%'
            OR url LIKE '%/events'
            OR url = source_url
            OR title LIKE '%October 2, 2025%'
            ORDER BY date
        ''')
        
        problematic_events = cursor.fetchall()
        conn.close()
        return problematic_events
    
    def get_duplicate_events(self):
        """Find duplicate events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find events with same title and date
        cursor.execute('''
            SELECT title, date, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM events 
            GROUP BY title, date 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        
        duplicates = cursor.fetchall()
        conn.close()
        return duplicates
    
    def is_generic_title(self, title):
        """Check if title is generic and not meaningful"""
        generic_patterns = [
            r'^Event$',
            r'^TBA$',
            r'.*Navigation.*',
            r'.*Search.*',
            r'^Events$',
            r'.*Upcoming.*Events.*',
            r'^.*Event.*$',
            r'.*\d{4}.*Seminar.*',  # Like "October 2, 2025Seminar"
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # Just a date
            r'^\w+\s+\d{1,2},\s+\d{4}$'  # Like "October 2, 2025"
        ]
        
        title_lower = title.lower()
        for pattern in generic_patterns:
            if re.match(pattern, title_lower):
                return True
        
        # Check if title is too short
        if len(title.strip()) < 5:
            return True
        
        return False
    
    def is_generic_url(self, url, source_url):
        """Check if URL is generic"""
        url_lower = url.lower()
        
        # Same as source URL
        if url == source_url:
            return True
        
        # Generic patterns
        generic_patterns = [
            '/events/',
            '/events',
            '/calendar/',
            '/calendar',
            '/search',
            '/filter',
            '/list/',
            '/archive/',
            '/past'
        ]
        
        for pattern in generic_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    def test_url_basic(self, url):
        """Basic URL validation"""
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code in [200, 301, 302]
        except:
            return False
    
    def fix_events(self):
        """Fix the regular events database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔍 Analyzing regular events...")
        
        # Get all events
        cursor.execute('SELECT id, title, url, date, source_url FROM events ORDER BY date')
        all_events = cursor.fetchall()
        
        print(f"📊 Total regular events: {len(all_events)}")
        
        events_to_delete = []
        
        for event_id, title, url, date, source_url in all_events:
            issues = []
            
            # Check for generic titles
            if self.is_generic_title(title):
                issues.append("Generic title")
            
            # Check for generic URLs
            if self.is_generic_url(url, source_url):
                issues.append("Generic URL")
            
            # Basic URL test for obvious failures
            if not self.test_url_basic(url):
                issues.append("URL not accessible")
            
            if issues:
                print(f"❌ Event {event_id}: {title}")
                print(f"   Issues: {', '.join(issues)}")
                print(f"   URL: {url}")
                events_to_delete.append(event_id)
            else:
                print(f"✅ Event {event_id}: {title}")
        
        # Handle duplicates
        print(f"\n🔍 Checking for duplicates...")
        duplicates = self.get_duplicate_events()
        
        for title, date, count, ids in duplicates:
            print(f"📋 Found {count} duplicates: {title} ({date})")
            id_list = [int(id) for id in ids.split(',')]
            # Keep the first one, delete the rest
            events_to_delete.extend(id_list[1:])
        
        # Delete problematic events
        if events_to_delete:
            print(f"\n🗑️  Deleting {len(events_to_delete)} problematic events...")
            placeholders = ','.join(['?' for _ in events_to_delete])
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', events_to_delete)
            deleted_count = cursor.rowcount
            print(f"✅ Deleted {deleted_count} events")
        
        # Fix date formats
        print(f"\n📅 Checking date formats...")
        cursor.execute('SELECT id, title, date FROM events WHERE date NOT LIKE "%-%-%" AND date != ""')
        bad_dates = cursor.fetchall()
        
        for event_id, title, date in bad_dates:
            print(f"⚠️  Event {event_id}: Bad date format '{date}' - {title}")
            # Try to parse the date
            try:
                # Handle formats like "June", "Nov"
                if date.lower() in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                   'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                                   'january', 'february', 'march', 'april', 'may', 'june',
                                   'july', 'august', 'september', 'october', 'november', 'december']:
                    # Set to first day of next month
                    month_map = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_map.get(date.lower())
                    if month:
                        current_year = datetime.now().year
                        if month < datetime.now().month:
                            current_year += 1
                        new_date = f"{current_year}-{month:02d}-01"
                        cursor.execute('UPDATE events SET date = ? WHERE id = ?', (new_date, event_id))
                        print(f"   Fixed to: {new_date}")
                    else:
                        # Delete if can't fix
                        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
                        print(f"   Deleted (unfixable)")
                else:
                    # Delete if can't parse
                    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
                    print(f"   Deleted (unfixable)")
            except Exception as e:
                print(f"   Error fixing date: {e}")
                cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Regular events cleanup completed!")
        
        # Show final stats
        self.show_stats()
    
    def show_stats(self):
        """Show final statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM events')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM events WHERE date >= date("now")')
        future_events = cursor.fetchone()[0]
        
        print(f"\n📈 Final Statistics:")
        print(f"   Total regular events: {total_events}")
        print(f"   Future events: {future_events}")
        
        # Show sample of remaining events
        cursor.execute('SELECT title, url, date FROM events WHERE date >= date("now") ORDER BY date LIMIT 10')
        remaining_events = cursor.fetchall()
        
        print(f"\n📋 Sample of remaining events:")
        for i, (title, url, date) in enumerate(remaining_events, 1):
            print(f"   {i}. {title} ({date})")
            print(f"      {url}")
        
        conn.close()


def main():
    """Main function"""
    print("🔧 Regular Events Fixer")
    print("=" * 50)
    
    fixer = RegularEventsFixer()
    fixer.fix_events()


if __name__ == "__main__":
    main()



