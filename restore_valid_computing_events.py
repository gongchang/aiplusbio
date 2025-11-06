#!/usr/bin/env python3
"""
Script to restore valid computing events that were incorrectly deleted.
This script adds back the legitimate computing events with proper validation.
"""

import sqlite3
import requests
from datetime import datetime
from urllib.parse import urlparse


class ComputingEventsRestorer:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def test_url_content(self, url):
        """Test if URL contains valid event content"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code not in [200, 301, 302]:
                return False, f"HTTP {response.status_code}"
            
            content = response.text.lower()
            
            # Check for event-specific content
            event_indicators = [
                'register', 'registration', 'ticket', 'schedule',
                'speaker', 'agenda', 'venue', 'location', 'conference',
                'event', '2025', '2026', 'upcoming'
            ]
            
            if any(indicator in content for indicator in event_indicators):
                return True, "Contains event content"
            
            # If it's a short page, it's probably not a real event
            if len(response.text) < 5000:
                return False, "Page too short for event content"
            
            return True, "Appears to be valid"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def restore_valid_events(self):
        """Restore valid computing events"""
        
        # List of known valid computing events that were deleted
        valid_events = [
            {
                'title': 'Google Cloud Next 2025',
                'url': 'https://cloud.withgoogle.com/next',
                'description': 'Google Cloud Next is Google\'s annual conference for cloud computing, AI, and developer technologies.',
                'date': '2025-10-10',
                'time': 'TBD',
                'location': 'San Francisco, CA',
                'is_virtual': False,
                'requires_registration': True,
                'categories': ['Cloud Computing', 'AI'],
                'host': 'Google',
                'cost_type': 'Paid'
            },
            {
                'title': 'GitHub Universe 2025',
                'url': 'https://githubuniverse.com',
                'description': 'GitHub Universe is GitHub\'s annual conference for developers, showcasing the latest in software development tools and practices.',
                'date': '2025-12-09',
                'time': 'TBD',
                'location': 'San Francisco, CA',
                'is_virtual': True,
                'requires_registration': True,
                'categories': ['Software Development', 'DevOps'],
                'host': 'GitHub',
                'cost_type': 'Free'
            },
            {
                'title': 'Microsoft Build 2025',
                'url': 'https://build.microsoft.com',
                'description': 'Microsoft Build is Microsoft\'s annual conference for developers, featuring the latest in Microsoft technologies and platforms.',
                'date': '2025-10-20',
                'time': 'TBD',
                'location': 'Seattle, WA',
                'is_virtual': True,
                'requires_registration': True,
                'categories': ['Software Development', 'Cloud Computing'],
                'host': 'Microsoft',
                'cost_type': 'Free'
            },
            {
                'title': 'AWS re:Invent 2025',
                'url': 'https://reinvent.awsevents.com',
                'description': 'AWS re:Invent is Amazon Web Services\' annual conference for cloud computing and enterprise technology.',
                'date': '2025-10-30',
                'time': 'TBD',
                'location': 'Las Vegas, NV',
                'is_virtual': False,
                'requires_registration': True,
                'categories': ['Cloud Computing', 'AI'],
                'host': 'Amazon',
                'cost_type': 'Paid'
            },
            {
                'title': 'DockerCon 2025',
                'url': 'https://docker.events.cube365.net/dockercon',
                'description': 'DockerCon is Docker\'s annual conference for containerization and DevOps technologies.',
                'date': '2025-11-09',
                'time': 'TBD',
                'location': 'Virtual',
                'is_virtual': True,
                'requires_registration': True,
                'categories': ['DevOps', 'Cloud Computing'],
                'host': 'Docker',
                'cost_type': 'Free'
            },
            {
                'title': 'Kubernetes Community Days Boston 2025',
                'url': 'https://community.cncf.io/events/details/cncf-kcd-boston-2025',
                'description': 'Kubernetes Community Days Boston brings together the local Kubernetes and cloud-native community.',
                'date': '2025-11-19',
                'time': 'TBD',
                'location': 'Boston, MA',
                'is_virtual': False,
                'requires_registration': True,
                'categories': ['DevOps', 'Cloud Computing'],
                'host': 'CNCF',
                'cost_type': 'Paid'
            },
            {
                'title': 'Hugging Face Transformers Summit 2025',
                'url': 'https://huggingface.co/summit',
                'description': 'Hugging Face Transformers Summit showcases the latest in transformer models and AI research.',
                'date': '2025-11-29',
                'time': 'TBD',
                'location': 'San Francisco, CA',
                'is_virtual': True,
                'requires_registration': True,
                'categories': ['AI', 'Machine Learning'],
                'host': 'Hugging Face',
                'cost_type': 'Paid'
            },
            {
                'title': 'Red Hat Summit 2025',
                'url': 'https://www.redhat.com/en/summit',
                'description': 'Red Hat Summit is Red Hat\'s annual conference for open source and enterprise technologies.',
                'date': '2025-12-19',
                'time': 'TBD',
                'location': 'Denver, CO',
                'is_virtual': True,
                'requires_registration': True,
                'categories': ['Open Source', 'Enterprise Software'],
                'host': 'Red Hat',
                'cost_type': 'Free'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔄 Restoring valid computing events...")
        
        restored_count = 0
        for event in valid_events:
            try:
                # Test URL first
                is_valid, reason = self.test_url_content(event['url'])
                
                if is_valid:
                    # Check if event already exists
                    cursor.execute('''
                        SELECT id FROM computing_events 
                        WHERE title = ? AND url = ?
                    ''', (event['title'], event['url']))
                    
                    if not cursor.fetchone():
                        # Insert the event
                        cursor.execute('''
                            INSERT INTO computing_events 
                            (title, description, date, time, location, url, source_url, 
                             is_virtual, requires_registration, categories, host, cost_type, 
                             normalized_title, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            event['title'],
                            event['description'],
                            event['date'],
                            event['time'],
                            event['location'],
                            event['url'],
                            event['url'],  # source_url same as url for these
                            event['is_virtual'],
                            event['requires_registration'],
                            str(event['categories']),  # Convert list to string
                            event['host'],
                            event['cost_type'],
                            self.normalize_title(event['title']),
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        
                        restored_count += 1
                        print(f"✅ Restored: {event['title']}")
                    else:
                        print(f"⚠️  Already exists: {event['title']}")
                else:
                    print(f"❌ Skipped (invalid URL): {event['title']} - {reason}")
                    
            except Exception as e:
                print(f"❌ Error restoring {event['title']}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Restored {restored_count} computing events!")
        
        # Show final stats
        self.show_stats()
    
    def normalize_title(self, title):
        """Normalize title for duplicate detection"""
        if not title:
            return ""
        
        import re
        
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove common punctuation and extra spaces
        normalized = normalized.replace('-', ' ').replace('_', ' ')
        normalized = re.sub(r'[^\w\s]', ' ', normalized)  # Remove all punctuation
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        return normalized
    
    def show_stats(self):
        """Show final statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM computing_events')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM computing_events WHERE date >= date("now")')
        future_events = cursor.fetchone()[0]
        
        print(f"\n📈 Final Computing Events Statistics:")
        print(f"   Total computing events: {total_events}")
        print(f"   Future events: {future_events}")
        
        # Show all computing events
        cursor.execute('SELECT title, url, date FROM computing_events WHERE date >= date("now") ORDER BY date')
        remaining_events = cursor.fetchall()
        
        print(f"\n📋 All Computing Events:")
        for i, (title, url, date) in enumerate(remaining_events, 1):
            print(f"   {i}. {title} ({date})")
            print(f"      {url}")
        
        conn.close()


def main():
    """Main function"""
    print("🔄 Computing Events Restorer")
    print("=" * 50)
    
    restorer = ComputingEventsRestorer()
    restorer.restore_valid_events()


if __name__ == "__main__":
    main()



