#!/usr/bin/env python3
"""
Aggressive Fix for Event Extraction Issues
This script handles cases where events have no descriptions and only date/time titles
"""

import sqlite3
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

def fix_aggressive():
    """Aggressively fix event extraction issues"""
    
    print("🔧 Aggressive Fix for Event Extraction Issues...")
    print("=" * 60)
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Get events with pure date/time titles and no descriptions
    cursor.execute('''
        SELECT id, title, url, source_url, description 
        FROM events 
        WHERE (title LIKE '%@%' OR title LIKE '%pm%' OR title LIKE '%am%')
           AND (description IS NULL OR description = '' OR LENGTH(description) < 10)
    ''')
    
    problematic_events = cursor.fetchall()
    print(f"🔍 Found {len(problematic_events)} events with date/time titles and no descriptions")
    
    fixed_count = 0
    
    for event_id, title, url, source_url, description in problematic_events:
        print(f"\n📅 Event ID: {event_id}")
        print(f"   Old title: {title}")
        
        # For events with no description, we need to create a generic title
        # based on the source and date
        new_title = create_generic_title(title, source_url)
        
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
            print(f"   ⚠️  Could not create better title")
    
    # Also fix events that have descriptions but still have bad titles
    cursor.execute('''
        SELECT id, title, url, source_url, description 
        FROM events 
        WHERE (title LIKE '%@%' OR title LIKE '%pm%' OR title LIKE '%am%')
           AND description IS NOT NULL 
           AND description != '' 
           AND LENGTH(description) >= 10
    ''')
    
    events_with_descriptions = cursor.fetchall()
    print(f"\n🔍 Found {len(events_with_descriptions)} events with date/time titles but have descriptions")
    
    for event_id, title, url, source_url, description in events_with_descriptions:
        print(f"\n📅 Event ID: {event_id}")
        print(f"   Old title: {title}")
        
        # Try to extract better title from description
        new_title = extract_better_title_from_description(description, source_url)
        
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
            print(f"   ⚠️  Could not extract better title from description")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fixed {fixed_count} title issues")
    return fixed_count

def create_generic_title(title, source_url):
    """Create a generic title for events with no description"""
    
    # Extract date and time from the title
    date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', title)
    time_match = re.search(r'@\s*(\d{1,2}:\d{2}\s*(am|pm)?)', title)
    
    if date_match:
        date_str = date_match.group(1)
    else:
        date_str = "Unknown Date"
    
    if time_match:
        time_str = time_match.group(1)
    else:
        time_str = ""
    
    # Create title based on source
    if 'biology.mit.edu' in source_url:
        base_title = "MIT Biology Event"
    elif 'csail.mit.edu' in source_url:
        base_title = "MIT CSAIL Event"
    elif 'cmsa.fas.harvard.edu' in source_url:
        base_title = "Harvard CMSA Event"
    elif 'bcs.mit.edu' in source_url:
        base_title = "MIT BCS Event"
    elif 'seas.harvard.edu' in source_url:
        base_title = "Harvard SEAS Event"
    elif 'dfci.harvard.edu' in source_url:
        base_title = "Dana-Farber Event"
    else:
        base_title = "Academic Event"
    
    if time_str:
        return f"{base_title} - {date_str} at {time_str}"
    else:
        return f"{base_title} - {date_str}"

def extract_better_title_from_description(description, source_url):
    """Extract a better title from description"""
    
    if not description:
        return None
    
    # Split description into sentences
    sentences = re.split(r'[.!?]+', description)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10 and len(sentence) < 200:
            # Check if sentence looks like a title (not just date/time)
            if not is_date_time_title(sentence):
                return sentence
    
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

if __name__ == '__main__':
    fix_aggressive()
    
    print("\n💡 Next Steps:")
    print("1. Review the fixed titles")
    print("2. Run 'python run.py' to test the improvements")
    print("3. Consider re-scraping to get better event data")
