#!/usr/bin/env python3
"""
Final fix for scraping issues:
1. Fix database constraints
2. Add better user agents
3. Implement duplicate checking
"""

import sqlite3
import random

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

def update_scraper():
    """Update scraper with better user agents"""
    print("🔧 Updating scraper with better user agents...")
    
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Update user agent
    old_ua = "'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'"
    new_ua = "'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'"
    
    if old_ua in content:
        content = content.replace(old_ua, new_ua)
        print("✅ Updated user agent")
    
    # Add better headers
    old_headers = "self.session.headers.update({"
    new_headers = '''self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1''
    
    if old_headers in content:
        content = content.replace(old_headers, new_headers)
        print("✅ Added comprehensive headers")
    
    with open('event_scraper.py', 'w') as f:
        f.write(content)

def add_duplicate_check():
    """Add duplicate checking to database"""
    print("🔧 Adding duplicate checking...")
    
    with open('database.py', 'r') as f:
        content = f.read()
    
    # Add event_exists method
    exists_method = '''
    def event_exists(self, event):
        """Check if event already exists"""
        try:
            cursor = self.conn.cursor()
            normalized_title = self.normalize_title(event.get('title', ''))
            date = event.get('date', '')
            source_url = event.get('source_url', '')
            
            cursor.execute('''
                SELECT COUNT(*) FROM events 
                WHERE normalized_title = ? AND date = ? AND source_url = ?
            ''', (normalized_title, date, source_url))
            
            return cursor.fetchone()[0] > 0
        except:
            return False
'''
    
    if 'def event_exists(' not in content:
        # Add at the end before the last closing
        content = content.replace('if __name__ == \'__main__\':', exists_method + '\nif __name__ == \'__main__\':')
        print("✅ Added event_exists method")
    
    with open('database.py', 'w') as f:
        f.write(content)

def main():
    print("🔧 Implementing Final Scraping Fixes...")
    print("=" * 50)
    
    fix_database()
    update_scraper()
    add_duplicate_check()
    
    print("\n🎉 Final fixes implemented!")
    print("💡 Improvements:")
    print("   - Better database constraints")
    print("   - Improved user agent and headers")
    print("   - Duplicate checking capability")
    print("\n🚀 Restart server to apply changes")

if __name__ == '__main__':
    main()
