#!/usr/bin/env python3
"""
Fix the problematic UNIQUE(url, date) constraint
"""

import sqlite3

def fix_url_constraint():
    """Remove the problematic UNIQUE(url, date) constraint"""
    
    print("🔧 Fixing problematic UNIQUE(url, date) constraint...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Get all data
    cursor.execute("SELECT * FROM events")
    all_data = cursor.fetchall()
    print(f"📊 Backing up {len(all_data)} events")
    
    # Create new table without the problematic constraint
    new_table_sql = '''
    CREATE TABLE events_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        time TEXT,
        location TEXT,
        url TEXT,
        source_url TEXT NOT NULL,
        is_virtual BOOLEAN DEFAULT FALSE,
        requires_registration BOOLEAN DEFAULT FALSE,
        categories TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        normalized_title TEXT
    )
    '''
    
    cursor.execute("DROP TABLE IF EXISTS events_new")
    cursor.execute(new_table_sql)
    
    # Copy all data to new table
    cursor.execute("SELECT * FROM events")
    columns = [description[0] for description in cursor.description]
    
    for row in all_data:
        placeholders = ','.join(['?' for _ in row])
        cursor.execute(f"INSERT INTO events_new VALUES ({placeholders})", row)
    
    # Replace old table with new one
    cursor.execute("DROP TABLE events")
    cursor.execute("ALTER TABLE events_new RENAME TO events")
    
    # Create a better unique constraint using normalized_title, date, and source_url
    cursor.execute('''
        CREATE UNIQUE INDEX idx_events_unique 
        ON events(normalized_title, date, source_url)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Fixed UNIQUE(url, date) constraint!")
    print("💡 Now using (normalized_title, date, source_url) for uniqueness")

def main():
    print("🔧 Fixing URL Constraint Issue...")
    print("=" * 40)
    
    fix_url_constraint()
    
    print("\n🎉 URL constraint issue fixed!")
    print("💡 The system now:")
    print("   - Removes problematic UNIQUE(url, date) constraint")
    print("   - Uses (normalized_title, date, source_url) for uniqueness")
    print("   - Allows multiple events with same URL but different titles/dates")
    print("\n🚀 Restart server to apply changes")

if __name__ == '__main__':
    main()
