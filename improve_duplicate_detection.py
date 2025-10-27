#!/usr/bin/env python3
"""
Improve duplicate detection and removal logic
"""

import sqlite3
import re
from difflib import SequenceMatcher

def normalize_text(text):
    """Normalize text for better comparison"""
    if not text:
        return ""
    # Convert to lowercase and remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    # Remove common punctuation
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    return normalized

def similarity_score(text1, text2):
    """Calculate similarity between two texts"""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()

def is_duplicate_event(event1, event2, threshold=0.85):
    """Check if two events are duplicates"""
    # Check exact matches first
    if (event1['title'] == event2['title'] and 
        event1['date'] == event2['date'] and 
        event1['time'] == event2['time'] and 
        event1['location'] == event2['location']):
        return True
    
    # Check similar titles with same date/time/location
    title_similarity = similarity_score(event1['title'], event2['title'])
    if (title_similarity >= threshold and 
        event1['date'] == event2['date'] and 
        event1['time'] == event2['time'] and 
        event1['location'] == event2['location']):
        return True
    
    # Check same title with same date/time (location might be different)
    if (title_similarity >= 0.95 and 
        event1['date'] == event2['date'] and 
        event1['time'] == event2['time']):
        return True
    
    return False

def update_database_duplicate_logic():
    """Update database with improved duplicate detection"""
    
    print("🔧 Updating database with improved duplicate detection...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Remove existing duplicates first
    print("🗑️  Removing existing duplicates...")
    
    # Find and remove duplicates based on title, date, time, location
    cursor.execute('''
        DELETE FROM events 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM events 
            GROUP BY title, date, time, location
        )
    ''')
    
    deleted_count = cursor.rowcount
    print(f"✅ Removed {deleted_count} duplicate events")
    
    # Create better unique constraint
    cursor.execute("DROP INDEX IF EXISTS idx_events_unique")
    cursor.execute('''
        CREATE UNIQUE INDEX idx_events_unique 
        ON events(title, date, time, location)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Updated database with improved duplicate detection")

def update_event_scraper_duplicate_logic():
    """Update event scraper with better duplicate detection"""
    
    print("🔧 Updating event scraper with intelligent duplicate detection...")
    
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Add duplicate detection function
    duplicate_function = '''
    def is_duplicate_event(self, new_event, existing_events):
        """Check if new event is a duplicate of existing events"""
        from difflib import SequenceMatcher
        import re
        
        def normalize_text(text):
            if not text:
                return ""
            normalized = re.sub(r'\\s+', ' ', text.lower().strip())
            normalized = re.sub(r'[^\\w\\s]', ' ', normalized)
            return normalized
        
        def similarity_score(text1, text2):
            if not text1 or not text2:
                return 0.0
            return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()
        
        for existing in existing_events:
            # Exact match
            if (new_event.get('title') == existing.get('title') and 
                new_event.get('date') == existing.get('date') and 
                new_event.get('time') == existing.get('time') and 
                new_event.get('location') == existing.get('location')):
                return True
            
            # Similar title with same date/time/location
            title_similarity = similarity_score(new_event.get('title', ''), existing.get('title', ''))
            if (title_similarity >= 0.85 and 
                new_event.get('date') == existing.get('date') and 
                new_event.get('time') == existing.get('time') and 
                new_event.get('location') == existing.get('location')):
                return True
            
            # Very similar title with same date/time
            if (title_similarity >= 0.95 and 
                new_event.get('date') == existing.get('date') and 
                new_event.get('time') == existing.get('time')):
                return True
        
        return False
'''
    
    # Add the function before the add_event method
    if 'def is_duplicate_event(' not in content:
        # Find a good place to insert (before add_event method)
        add_event_pos = content.find('def add_event(')
        if add_event_pos != -1:
            content = content[:add_event_pos] + duplicate_function + '\n    ' + content[add_event_pos:]
            print("✅ Added duplicate detection function")
    
    # Update the add_event method to use duplicate detection
    old_add_event = '''    def add_event(self, event):
        """Add an event to the database with duplicate checking"""
        try:
            # Check if event already exists before inserting
            if self.db.event_exists(event):
                self.logger.debug(f"Event already exists, skipping: {event.get('title', 'Unknown')[:50]}...")
                return True  # Consider it a success since we don't want duplicates
            
            self.db.add_event(event)
            return True
        except Exception as e:
            self.logger.error(f"Error adding event: {e}")
            return False'''
    
    new_add_event = '''    def add_event(self, event):
        """Add an event to the database with intelligent duplicate checking"""
        try:
            # Get existing events for duplicate checking
            existing_events = self.db.get_recent_events()
            
            # Check for duplicates using intelligent matching
            if self.is_duplicate_event(event, existing_events):
                self.logger.debug(f"Duplicate event detected, skipping: {event.get('title', 'Unknown')[:50]}...")
                return True  # Consider it a success since we don't want duplicates
            
            # Check if event already exists in database
            if self.db.event_exists(event):
                self.logger.debug(f"Event already exists in database, skipping: {event.get('title', 'Unknown')[:50]}...")
                return True
            
            self.db.add_event(event)
            return True
        except Exception as e:
            self.logger.error(f"Error adding event: {e}")
            return False'''
    
    if old_add_event in content:
        content = content.replace(old_add_event, new_add_event)
        print("✅ Updated add_event method with intelligent duplicate detection")
    
    with open('event_scraper.py', 'w') as f:
        f.write(content)

def update_database_methods():
    """Add get_recent_events method to database"""
    
    print("🔧 Adding get_recent_events method to database...")
    
    with open('database.py', 'r') as f:
        content = f.read()
    
    # Add get_recent_events method
    recent_events_method = '''
    def get_recent_events(self, days=30):
        """Get recent events for duplicate checking"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT title, date, time, location, source_url 
                FROM events 
                WHERE date >= date('now', '-{} days')
                ORDER BY created_at DESC
            '''.format(days))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'title': row[0],
                    'date': row[1],
                    'time': row[2],
                    'location': row[3],
                    'source_url': row[4]
                })
            
            return events
        except Exception as e:
            self.logger.error(f"Error getting recent events: {e}")
            return []
'''
    
    if 'def get_recent_events(' not in content:
        # Add at the end before the main block
        content = content.replace('if __name__ == \'__main__\':', recent_events_method + '\nif __name__ == \'__main__\':')
        print("✅ Added get_recent_events method")
    
    with open('database.py', 'w') as f:
        f.write(content)

def main():
    print("🔧 Implementing Intelligent Duplicate Detection...")
    print("=" * 55)
    
    update_database_duplicate_logic()
    update_event_scraper_duplicate_logic()
    update_database_methods()
    
    print("\n🎉 Intelligent duplicate detection implemented!")
    print("💡 The system now:")
    print("   - Automatically detects duplicates during scraping")
    print("   - Uses intelligent similarity matching (85-95% threshold)")
    print("   - Checks title, date, time, and location combinations")
    print("   - No need for separate duplicate removal scripts")
    print("   - Removes existing duplicates from database")
    print("\n🚀 Restart server to apply changes")

if __name__ == '__main__':
    main()
