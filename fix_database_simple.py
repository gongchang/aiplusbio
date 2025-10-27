#!/usr/bin/env python3
"""
Simple database fix to handle duplicate constraints
"""

import sqlite3

def fix_database():
    """Fix database to handle duplicates better"""
    
    print("🔧 Fixing database constraints...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Remove any problematic unique constraints
    try:
        cursor.execute("DROP INDEX IF EXISTS idx_events_url_date")
        print("✅ Removed old unique constraint index")
    except Exception as e:
        print(f"ℹ️  No old index to remove: {e}")
    
    # Create a better unique constraint
    try:
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique 
            ON events(normalized_title, date, source_url)
        ''')
        print("✅ Created new unique constraint on (normalized_title, date, source_url)")
    except Exception as e:
        print(f"ℹ️  Index already exists: {e}")
    
    # Check for and remove actual duplicates
    cursor.execute('''
        SELECT normalized_title, date, source_url, COUNT(*) as count
        FROM events 
        GROUP BY normalized_title, date, source_url
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    print(f"🔍 Found {len(duplicates)} duplicate groups")
    
    # Remove duplicates, keeping the most recent one
    for normalized_title, date, source_url, count in duplicates:
        cursor.execute('''
            SELECT id FROM events 
            WHERE normalized_title = ? AND date = ? AND source_url = ?
            ORDER BY created_at DESC
        ''', (normalized_title, date, source_url))
        
        event_ids = cursor.fetchall()
        
        if len(event_ids) > 1:
            # Keep the most recent one, delete the rest
            keep_id = event_ids[0][0]
            delete_ids = [event_id[0] for event_id in event_ids[1:]]
            
            placeholders = ','.join(['?' for _ in delete_ids])
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', delete_ids)
            
            print(f"🗑️  Removed {len(delete_ids)} duplicates for {normalized_title[:50]}...")
    
    conn.commit()
    conn.close()
    
    print("✅ Database constraints and duplicates fixed")

if __name__ == '__main__':
    fix_database()
