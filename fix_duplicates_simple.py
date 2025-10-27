#!/usr/bin/env python3
"""
Simple fix for duplicate detection
"""

import sqlite3

def remove_existing_duplicates():
    """Remove existing duplicates from database"""
    
    print("🔧 Removing existing duplicates...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Remove duplicates based on title, date, time, location
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
    
    # Update unique constraint
    cursor.execute("DROP INDEX IF EXISTS idx_events_unique")
    cursor.execute('''
        CREATE UNIQUE INDEX idx_events_unique 
        ON events(title, date, time, location)
    ''')
    
    conn.commit()
    conn.close()

def update_database_method():
    """Add method to get recent events"""
    
    print("🔧 Adding get_recent_events method...")
    
    with open('database.py', 'r') as f:
        content = f.read()
    
    # Add simple method
    method = '''
    def get_recent_events(self, days=30):
        """Get recent events for duplicate checking"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT title, date, time, location FROM events WHERE date >= date('now', '-{} days')".format(days))
            return [{'title': row[0], 'date': row[1], 'time': row[2], 'location': row[3]} for row in cursor.fetchall()]
        except:
            return []
'''
    
    if 'def get_recent_events(' not in content:
        content = content.replace('if __name__ == \'__main__\':', method + '\nif __name__ == \'__main__\':')
        with open('database.py', 'w') as f:
            f.write(content)
        print("✅ Added get_recent_events method")

def main():
    print("🔧 Fixing Duplicate Detection...")
    print("=" * 35)
    
    remove_existing_duplicates()
    update_database_method()
    
    print("\n🎉 Duplicate detection improved!")
    print("💡 Now using (title, date, time, location) for uniqueness")
    print("🚀 Restart server to apply changes")

if __name__ == '__main__':
    main()
