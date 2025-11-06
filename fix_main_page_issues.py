#!/usr/bin/env python3
"""
Script to fix the main page issues:
1. Remove non-event entries that are showing up on today's date
2. Fix category filtering issues
3. Ensure proper separation between main page and computing events
"""

import sqlite3
from datetime import datetime, date
import json


class MainPageIssuesFixer:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
    
    def identify_non_events(self):
        """Identify entries that are not actual events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔍 Identifying non-event entries...")
        
        # Get events that are clearly not events
        cursor.execute('SELECT id, title, source_url, institution FROM events')
        all_events = cursor.fetchall()
        
        non_events = []
        
        for event_id, title, source_url, institution in all_events:
            # Check for non-event patterns
            if self.is_non_event(title):
                non_events.append((event_id, title, source_url, institution))
        
        return non_events
    
    def is_non_event(self, title):
        """Check if a title is clearly not an event"""
        if not title:
            return True
        
        title_lower = title.lower()
        
        # Non-event patterns
        non_event_patterns = [
            # Department/research area names
            'computational science',
            'healthcare',
            'quantum convergence', 
            'robotics and multi-agent systems',
            'neuroscience',
            'biochemistry, biophysics, and structural biology',
            'cancer biology',
            'cell biology',
            'computational biology',
            'human disease',
            'immunology',
            'microbiology',
            'neurobiology',
            'stem cell and developmental biology',
            
            # General department/institute names
            'artificial intelligence',
            'cloud computing',
            'privacy & security',
            'data science',
            
            # Non-event content
            'undergraduate testimonials',
            'why mit biology?',
            'career development resources',
            'quantitative methods workshop',
            'remembering anthony j. sinskey',
            
            # Room/location names that aren't events
            'singleton auditorium',
            'duboc room',
            '68-180 and 181',
            
            # Generic content
            'poster session #1',
            'poster session #2',
            'this event is part of a series',
            'this event is part of a bi-weekly series'
        ]
        
        for pattern in non_event_patterns:
            if pattern in title_lower:
                return True
        
        # Check for very short titles that are likely not events
        if len(title.strip()) < 15:
            return True
        
        # Check for titles that are just research areas or departments
        research_areas = [
            'biology', 'chemistry', 'physics', 'mathematics', 'engineering',
            'computer science', 'data science', 'artificial intelligence',
            'neuroscience', 'immunology', 'cancer', 'genetics'
        ]
        
        # If title is just a research area name
        if title_lower.strip() in research_areas:
            return True
        
        return False
    
    def fix_today_events_issue(self):
        """Fix the issue where non-events are showing up on today's date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🗑️  Removing non-event entries...")
        
        # Get all events
        cursor.execute('SELECT id, title, date, source_url FROM events')
        all_events = cursor.fetchall()
        
        events_to_delete = []
        
        for event_id, title, event_date, source_url in all_events:
            if self.is_non_event(title):
                events_to_delete.append(event_id)
                print(f"❌ Removing: {title} ({event_date})")
        
        # Delete non-event entries
        if events_to_delete:
            placeholders = ','.join(['?' for _ in events_to_delete])
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', events_to_delete)
            deleted_count = cursor.rowcount
            print(f"\n✅ Deleted {deleted_count} non-event entries")
        
        conn.commit()
        conn.close()
    
    def fix_category_issues(self):
        """Fix category issues by ensuring proper category assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🏷️  Fixing category assignments...")
        
        # Get events without categories
        cursor.execute('SELECT id, title, source_url, categories FROM events WHERE categories = "[]" OR categories IS NULL')
        events_without_categories = cursor.fetchall()
        
        updated_count = 0
        
        for event_id, title, source_url, categories in events_without_categories:
            # Determine categories based on title and source
            new_categories = self.determine_categories(title, source_url)
            
            if new_categories:
                cursor.execute('''
                    UPDATE events 
                    SET categories = ?, updated_at = ?
                    WHERE id = ?
                ''', (json.dumps(new_categories), datetime.now().isoformat(), event_id))
                updated_count += 1
                print(f"✅ Updated categories for: {title}")
                print(f"   Categories: {new_categories}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Updated categories for {updated_count} events")
    
    def determine_categories(self, title, source_url):
        """Determine appropriate categories for an event"""
        title_lower = title.lower()
        source_lower = source_url.lower()
        
        categories = []
        
        # Computer Science related
        cs_keywords = [
            'computer science', 'cs', 'programming', 'software', 'algorithm',
            'artificial intelligence', 'ai', 'machine learning', 'data science',
            'computing', 'informatics', 'cyber', 'security', 'database',
            'networking', 'systems', 'engineering', 'technology'
        ]
        
        if any(keyword in title_lower for keyword in cs_keywords):
            categories.append('computer science')
        
        # Biology related
        bio_keywords = [
            'biology', 'bio', 'genetics', 'genomics', 'molecular', 'cell',
            'cancer', 'immunology', 'neuroscience', 'biochemistry',
            'biophysics', 'microbiology', 'developmental', 'evolution',
            'ecology', 'physiology', 'pathology', 'pharmacology'
        ]
        
        if any(keyword in title_lower for keyword in bio_keywords):
            categories.append('biology')
        
        # Source-based categorization
        if 'csail.mit.edu' in source_lower or 'cs' in source_lower:
            if 'computer science' not in categories:
                categories.append('computer science')
        
        if 'biology.mit.edu' in source_lower:
            if 'biology' not in categories:
                categories.append('biology')
        
        return categories
    
    def verify_separation(self):
        """Verify that main page and computing events are properly separated"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔍 Verifying page separation...")
        
        # Check that computing events are in separate table
        cursor.execute('SELECT COUNT(*) FROM computing_events')
        computing_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM events')
        regular_count = cursor.fetchone()[0]
        
        print(f"📊 Computing Events (separate table): {computing_count}")
        print(f"📊 Regular Events (main page): {regular_count}")
        
        # Check for any overlap (events that might be in both tables)
        cursor.execute('SELECT title FROM computing_events')
        computing_titles = {row[0] for row in cursor.fetchall()}
        
        cursor.execute('SELECT title FROM events')
        regular_titles = {row[0] for row in cursor.fetchall()}
        
        overlap = computing_titles & regular_titles
        if overlap:
            print(f"⚠️  Warning: Found {len(overlap)} events in both tables:")
            for title in list(overlap)[:5]:  # Show first 5
                print(f"   - {title}")
        else:
            print("✅ No overlap between computing events and regular events")
        
        conn.close()
        
        return len(overlap) == 0
    
    def show_final_stats(self):
        """Show final statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 FINAL STATISTICS")
        print("=" * 50)
        
        # Regular events
        cursor.execute('SELECT COUNT(*) FROM events')
        total_regular = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM events WHERE date >= date("now")')
        future_regular = cursor.fetchone()[0]
        
        # Computing events
        cursor.execute('SELECT COUNT(*) FROM computing_events')
        total_computing = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM computing_events WHERE date >= date("now")')
        future_computing = cursor.fetchone()[0]
        
        print(f'Main Page Events:')
        print(f'  Total: {total_regular}')
        print(f'  Future: {future_regular}')
        print(f'')
        print(f'Computing Events:')
        print(f'  Total: {total_computing}')
        print(f'  Future: {future_computing}')
        
        # Categories
        print(f'')
        print(f'📊 Categories:')
        cursor.execute('SELECT categories, COUNT(*) FROM events GROUP BY categories ORDER BY COUNT(*) DESC')
        category_counts = cursor.fetchall()
        for category, count in category_counts:
            print(f'  {category}: {count} events')
        
        # Events by date (check today)
        today = date.today()
        cursor.execute('SELECT COUNT(*) FROM events WHERE date = ?', (today.isoformat(),))
        today_count = cursor.fetchone()[0]
        print(f'')
        print(f'📅 Events on today ({today}): {today_count}')
        
        if today_count > 0:
            cursor.execute('SELECT title, institution FROM events WHERE date = ? LIMIT 5', (today.isoformat(),))
            today_events = cursor.fetchall()
            print(f'   Sample today events:')
            for title, institution in today_events:
                print(f'     • {title} ({institution})')
        
        conn.close()
    
    def run_fix(self):
        """Run all fixes"""
        print("🔧 MAIN PAGE ISSUES FIXER")
        print("=" * 50)
        
        # Fix non-event entries
        self.fix_today_events_issue()
        
        # Fix category issues
        self.fix_category_issues()
        
        # Verify separation
        separation_ok = self.verify_separation()
        
        # Show final stats
        self.show_final_stats()
        
        if separation_ok:
            print("\n✅ All issues fixed! Main page and computing events are properly separated.")
        else:
            print("\n⚠️  Some separation issues remain. Please review.")


def main():
    """Main function"""
    fixer = MainPageIssuesFixer()
    fixer.run_fix()


if __name__ == "__main__":
    main()



