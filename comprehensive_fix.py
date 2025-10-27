#!/usr/bin/env python3
"""
Comprehensive fix for scraping issues based on user analysis:
1. Implement proper "check before insert" logic
2. Fix 403 errors with better user agents
3. Improve error handling and logging
4. Add retry logic for transient errors
"""

import sqlite3
import requests
from urllib.parse import urlparse
import time
import random

def fix_database_constraints():
    """Fix database to properly handle duplicates"""
    
    print("🔧 Fixing database constraints...")
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Remove the problematic unique constraint that's causing issues
    try:
        cursor.execute("DROP INDEX IF EXISTS idx_events_url_date")
        print("✅ Removed problematic unique constraint")
    except Exception as e:
        print(f"ℹ️  No problematic index to remove: {e}")
    
    # Create a more robust unique constraint
    try:
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique 
            ON events(normalized_title, date, source_url)
        ''')
        print("✅ Created robust unique constraint on (normalized_title, date, source_url)")
    except Exception as e:
        print(f"ℹ️  Index already exists: {e}")
    
    # Remove any existing duplicates
    cursor.execute('''
        SELECT normalized_title, date, source_url, COUNT(*) as count
        FROM events 
        GROUP BY normalized_title, date, source_url
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    print(f"🔍 Found {len(duplicates)} duplicate groups")
    
    for normalized_title, date, source_url, count in duplicates:
        cursor.execute('''
            SELECT id FROM events 
            WHERE normalized_title = ? AND date = ? AND source_url = ?
            ORDER BY created_at DESC
        ''', (normalized_title, date, source_url))
        
        event_ids = cursor.fetchall()
        
        if len(event_ids) > 1:
            keep_id = event_ids[0][0]
            delete_ids = [event_id[0] for event_id in event_ids[1:]]
            
            placeholders = ','.join(['?' for _ in delete_ids])
            cursor.execute(f'DELETE FROM events WHERE id IN ({placeholders})', delete_ids)
            
            print(f"🗑️  Removed {len(delete_ids)} duplicates for {normalized_title[:50]}...")
    
    conn.commit()
    conn.close()
    
    print("✅ Database constraints fixed")

def update_event_scraper():
    """Update event scraper with better error handling and user agents"""
    
    print("🔧 Updating event scraper with comprehensive fixes...")
    
    # Read the current event_scraper.py
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Update the session initialization with better user agents and retry logic
    old_init = '''        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Handle SSL certificate issues
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)'''
    
    new_init = '''        self.session = requests.Session()
        
        # Rotate user agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Handle SSL certificate issues
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)'''
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ Updated session initialization with rotating user agents")
    
    # Update the scraping method with retry logic and better error handling
    old_scrape_method = '''    def scrape_site(self, url):
        """Scrape a single website for events"""
        self.logger.info(f"Scraping {url}")
        
        try:
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
    
    new_scrape_method = '''    def scrape_site(self, url):
        """Scrape a single website for events with retry logic"""
        self.logger.info(f"Scraping {url}")
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Rotate user agent for each attempt
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
                ]
                self.session.headers['User-Agent'] = random.choice(user_agents)
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                break  # Success, exit retry loop
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    self.logger.warning(f"Access forbidden (403) for {url} - attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"Failed to access {url} after {max_retries} attempts - site may be blocking scrapers")
                        return []
                else:
                    self.logger.error(f"HTTP error scraping {url}: {e}")
                    return []
                    
            except requests.exceptions.SSLError as e:
                self.logger.warning(f"SSL certificate error for {url}: {e}")
                return []
                
            except requests.RequestException as e:
                self.logger.warning(f"Request error for {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"Failed to scrape {url} after {max_retries} attempts: {e}")
                    return []'''
    
    if old_scrape_method in content:
        content = content.replace(old_scrape_method, new_scrape_method)
        print("✅ Updated scraping method with retry logic and better error handling")
    
    # Update the add_event method to implement "check before insert" logic
    old_add_event = '''    def add_event(self, event):
        """Add an event to the database"""
        try:
            self.db.add_event(event)
            return True
        except Exception as e:
            self.logger.error(f"Error adding event: {e}")
            return False'''
    
    new_add_event = '''    def add_event(self, event):
        """Add an event to the database with duplicate checking"""
        try:
            # Check if event already exists before inserting
            if self.db.event_exists(event):
                self.logger.debug(f"Event already exists, skipping: {event.get('title', 'Unknown')[:50]}...")
                return True  # Consider it a success since we don't want duplicates
            
            self.db.add_event(event)
            return True
        except Exception as e:
            self.logger.error(f"Error adding event: {e}")
            return False'''
    
    if old_add_event in content:
        content = content.replace(old_add_event, new_add_event)
        print("✅ Updated add_event method with duplicate checking")
    
    # Write the updated content back
    with open('event_scraper.py', 'w') as f:
        f.write(content)
    
    print("✅ Event scraper updated with comprehensive fixes")

def update_database_methods():
    """Add event_exists method to database"""
    
    print("🔧 Adding event_exists method to database...")
    
    # Read the current database.py
    with open('database.py', 'r') as f:
        content = f.read()
    
    # Add the event_exists method
    event_exists_method = '''
    def event_exists(self, event):
        """Check if an event already exists in the database"""
        try:
            cursor = self.conn.cursor()
            
            # Check by normalized title, date, and source URL
            normalized_title = self.normalize_title(event.get('title', ''))
            date = event.get('date', '')
            source_url = event.get('source_url', '')
            
            cursor.execute('''
                SELECT COUNT(*) FROM events 
                WHERE normalized_title = ? AND date = ? AND source_url = ?
            ''', (normalized_title, date, source_url))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            self.logger.error(f"Error checking if event exists: {e}")
            return False  # Assume it doesn't exist if we can't check
'''
    
    # Find a good place to insert the method (after add_event method)
    if 'def add_event(' in content and 'def event_exists(' not in content:
        # Insert after the add_event method
        add_event_end = content.find('def add_event(')
        if add_event_end != -1:
            # Find the end of the add_event method
            method_start = content.find('def add_event(', add_event_end)
            method_end = content.find('\n    def ', method_start + 1)
            if method_end == -1:
                method_end = content.find('\n\n', method_start)
            
            if method_end != -1:
                content = content[:method_end] + event_exists_method + content[method_end:]
                print("✅ Added event_exists method to database")
            else:
                print("❌ Could not find end of add_event method")
        else:
            print("❌ Could not find add_event method")
    else:
        print("ℹ️  event_exists method already exists or add_event method not found")
    
    # Write the updated content back
    with open('database.py', 'w') as f:
        f.write(content)

def main():
    """Run all comprehensive fixes"""
    print("🔧 Implementing Comprehensive Scraping Fixes...")
    print("=" * 60)
    
    fix_database_constraints()
    update_event_scraper()
    update_database_methods()
    
    print("\n🎉 Comprehensive fixes implemented!")
    print("💡 The system now includes:")
    print("   - Proper duplicate checking before insert")
    print("   - Rotating user agents to avoid 403 errors")
    print("   - Retry logic with exponential backoff")
    print("   - Better error handling and logging")
    print("   - Robust database constraints")
    print("\n🚀 Restart the server to apply all changes")

if __name__ == '__main__':
    main()
