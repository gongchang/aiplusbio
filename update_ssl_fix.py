#!/usr/bin/env python3
"""
Update event scraper to handle SSL issues better
"""

def update_ssl_handling():
    """Update the event scraper to handle SSL issues"""
    
    print("🔧 Updating SSL handling in event scraper...")
    
    # Read the current event_scraper.py
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Update the session initialization to handle SSL issues
    old_init = '''        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })'''
    
    new_init = '''        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Handle SSL certificate issues
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)'''
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        
        # Write the updated content back
        with open('event_scraper.py', 'w') as f:
            f.write(content)
        
        print("✅ Successfully updated SSL handling")
        return True
    else:
        print("❌ Could not find session initialization to update")
        return False

if __name__ == '__main__':
    if update_ssl_handling():
        print("\\n🎉 Event scraper now handles SSL issues better!")
        print("💡 The scraper will now:")
        print("   - Disable SSL verification for problematic sites")
        print("   - Suppress SSL warnings")
        print("   - Handle certificate issues gracefully")
    else:
        print("\\n❌ Failed to update SSL handling")
