#!/usr/bin/env python3
"""
Simple fix for scraping issues
"""

import sqlite3

def fix_database():
    """Fix database constraints"""
    print("🔧 Fixing database constraints...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Remove problematic constraints
    try:
        cursor.execute("DROP INDEX IF EXISTS idx_events_url_date")
        print("✅ Removed problematic unique constraint")
    except:
        pass
    
    # Create better constraint
    try:
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique 
            ON events(normalized_title, date, source_url)
        ''')
        print("✅ Created robust unique constraint")
    except:
        pass
    
    conn.commit()
    conn.close()

def update_user_agent():
    """Update user agent in scraper"""
    print("🔧 Updating user agent...")
    
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Replace old user agent with a better one
    content = content.replace(
        "Chrome/91.0.4472.124 Safari/537.36",
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    with open('event_scraper.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated user agent")

def main():
    print("🔧 Implementing Simple Scraping Fixes...")
    print("=" * 40)
    
    fix_database()
    update_user_agent()
    
    print("\n🎉 Simple fixes implemented!")
    print("💡 Improvements:")
    print("   - Better database constraints")
    print("   - Updated user agent")
    print("\n🚀 Restart server to apply changes")

if __name__ == '__main__':
    main()
