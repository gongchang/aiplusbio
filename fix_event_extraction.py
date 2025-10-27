#!/usr/bin/env python3
"""
Fix for Event Extraction Issues
Addresses:
1. Title extraction - events showing time/date instead of actual titles
2. URL extraction - events linking to source pages instead of specific event pages
"""

import sqlite3
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

def fix_event_extraction():
    """Fix event extraction issues in the database"""
    
    print("🔧 Fixing Event Extraction Issues...")
    print("=" * 60)
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Get all events with problematic titles
    cursor.execute('''
        SELECT id, title, url, source_url, description 
        FROM events 
        WHERE title LIKE '%@%' 
           OR title LIKE '%pm%' 
           OR title LIKE '%am%'
           OR title LIKE '%2024%'
           OR title LIKE '%2025%'
           OR title LIKE '%January%'
           OR title LIKE '%February%'
           OR title LIKE '%March%'
           OR title LIKE '%April%'
           OR title LIKE '%May%'
           OR title LIKE '%June%'
           OR title LIKE '%July%'
           OR title LIKE '%August%'
           OR title LIKE '%September%'
           OR title LIKE '%October%'
           OR title LIKE '%November%'
           OR title LIKE '%December%'
    ''')
    
    problematic_events = cursor.fetchall()
    print(f"🔍 Found {len(problematic_events)} events with problematic titles")
    
    fixed_count = 0
    
    for event_id, title, url, source_url, description in problematic_events:
        print(f"\n📅 Event ID: {event_id}")
        print(f"   Old title: {title}")
        
        # Try to extract better title from description
        new_title = extract_better_title(title, description)
        
        if new_title and new_title != title:
            # Update the title
            cursor.execute('''
                UPDATE events 
                SET title = ?, updated_at = ?
                WHERE id = ?
            ''', (new_title, datetime.now().isoformat(), event_id))
            
            print(f"   ✅ New title: {new_title}")
            fixed_count += 1
        else:
            print(f"   ⚠️  Could not find better title")
    
    # Fix URL issues
    print(f"\n🔗 Fixing URL issues...")
    
    cursor.execute('''
        SELECT id, title, url, source_url 
        FROM events 
        WHERE url = source_url 
           OR url LIKE '%#%'
           OR url LIKE '%index%'
    ''')
    
    url_problems = cursor.fetchall()
    print(f"🔗 Found {len(url_problems)} events with URL issues")
    
    url_fixed_count = 0
    
    for event_id, title, url, source_url in url_problems:
        print(f"\n🔗 Event ID: {event_id}")
        print(f"   Title: {title[:50]}...")
        print(f"   Current URL: {url}")
        
        # For now, we'll mark these for manual review
        # In a real implementation, you might want to re-scrape these events
        print(f"   ⚠️  URL needs manual review")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fixed {fixed_count} title issues")
    print(f"⚠️  {len(url_problems)} URL issues need manual review")
    
    return fixed_count, len(url_problems)

def extract_better_title(title, description):
    """Extract a better title from description or improve existing title"""
    
    # If title looks like a date/time, try to find better title in description
    if is_date_time_title(title):
        # Look for meaningful text in description
        if description:
            # Split description into sentences
            sentences = re.split(r'[.!?]+', description)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and len(sentence) < 200:
                    # Check if sentence looks like a title (not just date/time)
                    if not is_date_time_title(sentence):
                        return sentence
    
    # Try to clean up the existing title
    cleaned_title = clean_title(title)
    if cleaned_title and not is_date_time_title(cleaned_title):
        return cleaned_title
    
    return None

def is_date_time_title(text):
    """Check if text looks like a date/time instead of a title"""
    if not text:
        return True
    
    text_lower = text.lower()
    
    # Check for date/time patterns
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
        r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}',
        r'\d{1,2}:\d{2}\s*(am|pm)',
        r'@\s*\d{1,2}:\d{2}',
        r'\d{1,2}:\d{2}',
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # Check if text is mostly numbers and common date/time words
    words = text.split()
    if len(words) <= 3:
        date_time_words = ['am', 'pm', 'at', '@', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
        date_time_count = sum(1 for word in words if word.lower() in date_time_words or word.isdigit())
        if date_time_count >= len(words) * 0.7:  # 70% or more are date/time words
            return True
    
    return False

def clean_title(title):
    """Clean up a title by removing date/time information"""
    if not title:
        return None
    
    # Remove common date/time patterns from the beginning or end
    patterns_to_remove = [
        r'^\d{1,2}/\d{1,2}/\d{4}\s*[-–—]\s*',
        r'^\d{4}-\d{2}-\d{2}\s*[-–—]\s*',
        r'^\w+\s+\d{1,2},?\s+\d{4}\s*[-–—]\s*',
        r'\s*[-–—]\s*\d{1,2}/\d{1,2}/\d{4}$',
        r'\s*[-–—]\s*\d{4}-\d{2}-\d{2}$',
        r'\s*[-–—]\s*\w+\s+\d{1,2},?\s+\d{4}$',
        r'\s*@\s*\d{1,2}:\d{2}\s*(am|pm)?$',
        r'\s*\d{1,2}:\d{2}\s*(am|pm)?$',
    ]
    
    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    cleaned = cleaned.strip()
    
    # Remove leading/trailing punctuation
    cleaned = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', cleaned)
    
    return cleaned if cleaned else None

def show_problematic_events():
    """Show examples of problematic events"""
    print("\n📋 Examples of Problematic Events:")
    print("-" * 60)
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, url, source_url 
        FROM events 
        WHERE title LIKE '%@%' 
           OR title LIKE '%pm%' 
           OR title LIKE '%am%'
        LIMIT 10
    ''')
    
    examples = cursor.fetchall()
    
    for i, (title, url, source_url) in enumerate(examples, 1):
        print(f"{i}. Title: {title}")
        print(f"   URL: {url}")
        print(f"   Source: {source_url}")
        print()
    
    conn.close()

if __name__ == '__main__':
    show_problematic_events()
    fix_event_extraction()
    
    print("\n💡 Next Steps:")
    print("1. Review the fixed titles")
    print("2. For URL issues, consider re-scraping those specific events")
    print("3. Run 'python run.py' to test the improvements")
