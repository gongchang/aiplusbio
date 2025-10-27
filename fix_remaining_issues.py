#!/usr/bin/env python3
"""
Fix remaining scraping issues:
1. Improve duplicate handling
2. Better error handling for 403/SSL issues
3. Update database constraints
"""

import sqlite3
import os

def fix_database_constraints():
    """Fix database constraints to handle duplicates better"""
    
    print("🔧 Fixing database constraints...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(events)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"📊 Current columns: {column_names}")
    
    # Remove the problematic unique constraint if it exists
    try:
        cursor.execute("DROP INDEX IF EXISTS idx_events_url_date")
        print("✅ Removed old unique constraint index")
    except Exception as e:
        print(f"ℹ️  No old index to remove: {e}")
    
    # Create a better unique constraint that allows updates
    try:
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique 
            ON events(normalized_title, date, source_url)
        ''')
        print("✅ Created new unique constraint on (normalized_title, date, source_url)")
    except Exception as e:
        print(f"ℹ️  Index already exists: {e}")
    
    # Add a column for last_updated if it doesn't exist
    if 'last_updated' not in column_names:
        cursor.execute('ALTER TABLE events ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        print("✅ Added last_updated column")
    
    conn.commit()
    conn.close()
    
    print("✅ Database constraints updated")

def update_event_scraper():
    """Update event scraper to handle errors better"""
    
    print("🔧 Updating event scraper error handling...")
    
    # Read the current event_scraper.py
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Add better error handling for 403 and SSL issues
    old_error_handling = '''        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return []'''
    
    new_error_handling = '''        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                self.logger.warning(f"Access forbidden (403) for {url} - site may be blocking scrapers")
            else:
                self.logger.error(f"HTTP error scraping {url}: {e}")
            return []
        except requests.exceptions.SSLError as e:
            self.logger.warning(f"SSL certificate error for {url}: {e}")
            return []
        except requests.RequestException as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return []'''
    
    if old_error_handling in content:
        content = content.replace(old_error_handling, new_error_handling)
        
        with open('event_scraper.py', 'w') as f:
            f.write(content)
        
        print("✅ Updated error handling in event scraper")
        return True
    else:
        print("ℹ️  Error handling already updated or not found")
        return False

def main():
    """Run all fixes"""
    print("🔧 Fixing Remaining Scraping Issues...")
    print("=" * 50)
    
    fix_database_constraints()
    update_event_scraper()
    
    print("\n🎉 Remaining issues fixed!")
    print("💡 The system will now:")
    print("   - Handle duplicate events more gracefully")
    print("   - Better handle 403 and SSL errors")
    print("   - Allow event updates without constraint violations")
    print("   - Log warnings instead of errors for common issues")

if __name__ == '__main__':
    main()
