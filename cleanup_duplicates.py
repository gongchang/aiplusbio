#!/usr/bin/env python3
"""
Script to clean up duplicate events from the database
"""

import sqlite3
import json
from datetime import datetime

def cleanup_duplicates():
    """Remove duplicate events from the database"""
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    print("🧹 Cleaning up duplicate events...")
    
    # First, let's see how many events we have
    cursor.execute('SELECT COUNT(*) FROM events')
    total_events = cursor.fetchone()[0]
    print(f"📊 Total events before cleanup: {total_events}")
    
    # Find duplicates based on normalized title, date, and source
    cursor.execute('''
        SELECT normalized_title, date, source_url, COUNT(*) as count
        FROM events 
        WHERE normalized_title IS NOT NULL
        GROUP BY normalized_title, date, source_url
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    print(f"🔍 Found {len(duplicates)} groups of duplicates")
    
    # Remove duplicates, keeping the most recent one
    for duplicate in duplicates:
        normalized_title, date, source_url, count = duplicate
        
        # Get all events in this duplicate group
        cursor.execute('''
            SELECT id, updated_at FROM events 
            WHERE normalized_title = ? AND date = ? AND source_url = ?
            ORDER BY updated_at DESC
        ''', (normalized_title, date, source_url))
        
        events = cursor.fetchall()
        
        # Keep the most recent one, delete the rest
        if len(events) > 1:
            keep_id = events[0][0]  # Most recent
            delete_ids = [event[0] for event in events[1:]]
            
            # Delete duplicates
            placeholders = ','.join(['?' for _ in delete_ids])
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', delete_ids)
            
            print(f"🗑️  Removed {len(delete_ids)} duplicates for: {normalized_title[:50]}...")
    
    # Update normalized titles for events that don't have them
    cursor.execute('''
        UPDATE events 
        SET normalized_title = LOWER(REPLACE(REPLACE(title, '-', ' '), '_', ' '))
        WHERE normalized_title IS NULL
    ''')
    
    # Commit changes
    conn.commit()
    
    # Check final count
    cursor.execute('SELECT COUNT(*) FROM events')
    final_count = cursor.fetchone()[0]
    
    print(f"✅ Cleanup complete! Events after cleanup: {final_count}")
    print(f"🗑️  Removed {total_events - final_count} duplicate events")
    
    conn.close()

if __name__ == '__main__':
    cleanup_duplicates() 