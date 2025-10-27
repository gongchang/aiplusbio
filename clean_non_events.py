#!/usr/bin/env python3
"""
Script to clean up non-event content that was accidentally restored.
This script removes navigation links, contact info, and other non-event content.
"""

import sqlite3
import re


class NonEventsCleaner:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
    
    def is_non_event_content(self, title):
        """Check if title is non-event content"""
        if not title or not title.strip():
            return True
        
        title = title.strip()
        
        # Navigation and UI elements
        navigation_patterns = [
            'CONNECT WITH US', 'From the Director', 'Our Impact', 'Directions & Parking',
            'Our Patron', 'CENTERS & INITIATIVES', 'NEWS & EVENTS', 'GET INVOLVED',
            'Connect with Us', 'RESOURCES & SERVICES', 'Support & Tools', 'Space & Facilities',
            'Online Forms', 'All Topics', 'Featured Events', 'Submit a listing',
            'Support Biology', 'Contact Us', 'Honors and Awards', 'Employment Opportunities',
            'Current Faculty', 'In Memoriam', 'Areas of Research', 'Core Facilities',
            'Video Gallery', 'Faculty Resources', 'Undergraduate', 'Why Biology',
            'Major/Minor Requirements', 'General Institute Requirement', 'Advanced Standing Exam',
            'Transfer Credit', 'Current Students', 'Subject Offerings', 'Research Opportunities',
            'Biology Undergraduate Student Association', 'Career Development', 'Why MIT Biology',
            'Diversity in the Graduate Program', 'NIH Training Grant', 'Career Outcomes',
            'Graduate Testimonials', 'Prospective Students', 'Application Process',
            'Interdisciplinary and Joint Degree Programs', 'Living in Cambridge',
            'Graduate Manual', 'Graduate Teaching', 'Biology Graduate Student Council',
            'BioPals Program', 'Postdoctoral', 'Life as a Postdoc', 'Postdoc Associations',
            'Postdoc Testimonials', 'Workshops for MIT Biology Postdocs',
            'Responsible Conduct of Research', 'Postdoc Resources', 'Non-MIT Undergraduates',
            'High School Students and Teachers', 'Summer Workshop for Teachers',
            'MIT Field Trips', 'LEAH Knox Scholars Program', 'Additional Resources',
            'MITx Biology', 'Department Calendar', 'EHS and Facilities',
            'Remembering Anthony J. Sinskey', 'Resources for MD/PhD Students',
            'Preliminary Exam Guidelines', 'Thesis Committee Meetings',
            'Guidelines for Graduating', 'Mentoring Students and Early-Career Scientists',
            'BSG-MSRP-Bio Gould Fellows', 'Calendar of Events'
        ]
        
        if title in navigation_patterns:
            return True
        
        # Contact information
        contact_patterns = [
            r'^\d{3}-\d{3}-\d{4}$',  # Phone numbers
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email addresses
            r'^\d+\s+[a-zA-Z\s]+,\s+\d{5}$',  # Addresses
        ]
        
        for pattern in contact_patterns:
            if re.match(pattern, title):
                return True
        
        # Short titles that are likely navigation
        if len(title) < 10:
            return True
        
        # Titles that are just locations or room numbers
        if re.match(r'^[A-Z0-9\s,-]+$', title) and len(title) < 20:
            return True
        
        # Titles that are just series names without specific events
        series_patterns = [
            r'^.*Seminar Series.*$',
            r'^.*Colloquium Series.*$',
            r'^.*Workshop Series.*$'
        ]
        
        for pattern in series_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                return True
        
        return False
    
    def clean_non_events(self):
        """Remove non-event content from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🧹 Cleaning up non-event content...")
        
        # Get all events
        cursor.execute('SELECT id, title FROM events ORDER BY id')
        all_events = cursor.fetchall()
        
        events_to_delete = []
        
        for event_id, title in all_events:
            if self.is_non_event_content(title):
                events_to_delete.append(event_id)
                print(f"❌ Removing: {title}")
        
        # Delete non-event content
        if events_to_delete:
            placeholders = ','.join(['?' for _ in events_to_delete])
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', events_to_delete)
            deleted_count = cursor.rowcount
            print(f"\n🗑️  Deleted {deleted_count} non-event entries")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Cleanup completed!")
        
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
        print(f"   Total events: {total_events}")
        print(f"   Future events: {future_events}")
        
        # Show events by source
        cursor.execute('SELECT source_url, COUNT(*) FROM events GROUP BY source_url ORDER BY COUNT(*) DESC')
        source_counts = cursor.fetchall()
        
        print(f"\n📊 Events by Source:")
        for source, count in source_counts:
            print(f"   {source}: {count} events")
        
        # Show sample events
        print(f"\n📋 Sample Events:")
        cursor.execute('SELECT title, url, date FROM events WHERE date >= date("now") ORDER BY date LIMIT 10')
        sample_events = cursor.fetchall()
        for i, (title, url, date) in enumerate(sample_events, 1):
            print(f"   {i}. {title} ({date})")
            print(f"      {url}")
        
        conn.close()


def main():
    """Main function"""
    print("🧹 Non-Events Cleaner")
    print("=" * 50)
    
    cleaner = NonEventsCleaner()
    cleaner.clean_non_events()


if __name__ == "__main__":
    main()


