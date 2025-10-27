#!/usr/bin/env python3
"""
Integrate bullet-point event handling into the main event scraper
"""

import re
from bs4 import BeautifulSoup

def extract_bullet_point_events(soup, base_url):
    """
    Extract events from bullet-point structures (like IAIFI)
    This can be integrated into the main event_scraper.py
    """
    events = []
    
    # Find all list items that might contain events
    all_list_items = soup.find_all('li')
    
    for item in all_list_items:
        event = extract_event_from_bullet_item(item, base_url)
        if event:
            events.append(event)
    
    # Remove duplicates
    unique_events = []
    seen = set()
    
    for event in events:
        key = (event['title'], event['date'])
        if key not in seen:
            seen.add(key)
            unique_events.append(event)
    
    return unique_events

def extract_event_from_bullet_item(item, base_url):
    """Extract event from a bullet point item"""
    try:
        # Get text content
        text_content = item.get_text(strip=True)
        
        # Skip short content
        if len(text_content) < 30:
            return None
        
        # Extract date
        date = extract_date_from_text(text_content)
        if not date:
            return None
        
        # Extract speaker/title
        speaker = extract_speaker_from_item(item)
        title = extract_title_from_item(item, text_content, speaker)
        
        if not title:
            return None
        
        # Extract time and location
        time_location = extract_time_location_from_text(text_content)
        
        # Create final title
        if time_location and title:
            final_title = f"{title} ({time_location})"
        else:
            final_title = title
        
        # Extract URL
        link = item.find('a', href=True)
        event_url = link['href'] if link else base_url
        
        return {
            'title': final_title,
            'date': date,
            'url': event_url,
            'description': "",
            'source_url': base_url
        }
        
    except Exception as e:
        return None

def extract_date_from_text(text):
    """Extract date from text"""
    date_patterns = [
        r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group()
    
    return None

def extract_speaker_from_item(item):
    """Extract speaker from bold elements"""
    bold_elements = item.find_all(['strong', 'b'])
    if bold_elements:
        speaker = bold_elements[0].get_text(strip=True)
        # Remove date from speaker
        speaker = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', speaker, flags=re.I).strip()
        if speaker and speaker.lower() not in ['speaker to be announced', 'title to come']:
            return speaker
    return None

def extract_title_from_item(item, text_content, speaker):
    """Extract title from item"""
    if speaker:
        return speaker
    
    # Remove date from text
    clean_text = re.sub(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', text_content, flags=re.I)
    clean_text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '', clean_text, flags=re.I)
    
    # Take first meaningful line
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    for line in lines:
        if line and len(line) > 10 and line.lower() not in ['speaker to be announced', 'title to come', 'abstract to come']:
            return line
    
    return None

def extract_time_location_from_text(text):
    """Extract time and location from text"""
    time_location = ""
    
    # Extract time
    time_pattern = r'\d{1,2}:\d{2}(?:am|pm)–\d{1,2}:\d{2}(?:am|pm)'
    time_match = re.search(time_pattern, text, re.I)
    if time_match:
        time_location = time_match.group()
    
    # Extract location
    location_pattern = r'(?:MIT|Harvard|Room|Building|Hall|Center)[^,]*'
    location_match = re.search(location_pattern, text, re.I)
    if location_match:
        location = location_match.group()
        if time_location:
            time_location += ", " + location
        else:
            time_location = location
    
    return time_location

def detect_bullet_point_structure(soup):
    """
    Detect if a page uses bullet-point event structure
    Returns True if bullet-point structure is detected
    """
    # Look for common indicators of bullet-point event structures
    indicators = [
        # Look for sections with "Upcoming" in headings
        soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], string=re.compile(r'upcoming', re.I)),
        # Look for list items with dates
        soup.find_all('li', string=re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', re.I)),
        # Look for bullet points with speaker names in bold
        soup.find_all('li', lambda text: text and text.find(['strong', 'b']))
    ]
    
    # If any indicator is found, likely bullet-point structure
    return any(len(indicator) > 0 for indicator in indicators)

def main():
    """Test the bullet-point extraction functions"""
    print("🔧 Bullet-Point Event Extraction Functions")
    print("=" * 50)
    print("✅ Functions ready for integration into main event_scraper.py")
    print("\n📋 Available functions:")
    print("  • extract_bullet_point_events(soup, base_url)")
    print("  • detect_bullet_point_structure(soup)")
    print("  • extract_event_from_bullet_item(item, base_url)")
    print("\n🔧 Integration instructions:")
    print("1. Add these functions to event_scraper.py")
    print("2. In scrape_site(), add bullet-point detection:")
    print("   if detect_bullet_point_structure(soup):")
    print("       events = extract_bullet_point_events(soup, url)")
    print("   else:")
    print("       events = extract_events_from_page(soup, url)")

if __name__ == "__main__":
    main()










