#!/usr/bin/env python3
"""
Script to clear all computing events from the database.
Useful for testing or when you want to start fresh.
"""

import sqlite3
from database import Database

def clear_computing_events():
    """Clear all computing events from the database"""
    try:
        db = Database()
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Clear all computing events
        cursor.execute('DELETE FROM computing_events')
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleared {deleted_count} computing events from database")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error clearing computing events: {e}")
        return 0

def clear_all_events():
    """Clear all events (both regular and computing events) from the database"""
    try:
        db = Database()
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Clear all events
        cursor.execute('DELETE FROM events')
        regular_events_deleted = cursor.rowcount
        
        # Clear all computing events
        cursor.execute('DELETE FROM computing_events')
        computing_events_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleared {regular_events_deleted} regular events")
        print(f"✅ Cleared {computing_events_deleted} computing events")
        return regular_events_deleted + computing_events_deleted
        
    except Exception as e:
        print(f"❌ Error clearing events: {e}")
        return 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("🗑️  Clearing ALL events from database...")
        clear_all_events()
    else:
        print("🗑️  Clearing computing events from database...")
        clear_computing_events()
    
    print("✅ Database cleanup completed!")



