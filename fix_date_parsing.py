#!/usr/bin/env python3

import sqlite3
from datetime import datetime
import re

def parse_date(date_str):
    """Parse various date formats and convert to ISO format"""
    if not date_str:
        return None
    
    # Try to parse different date formats
    date_patterns = [
        r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # "September 9, 2025" or "September 9 2025"
        r'(\d{4})-(\d{2})-(\d{2})',        # "2025-09-09"
        r'(\d{1,2})/(\d{1,2})/(\d{4})',    # "9/9/2025"
    ]
    
    month_names = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str.lower())
        if match:
            if len(match.groups()) == 3:
                if match.group(1).isdigit():
                    # Format: YYYY-MM-DD or MM/DD/YYYY
                    if len(match.group(1)) == 4:
                        # YYYY-MM-DD
                        return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    else:
                        # MM/DD/YYYY
                        return f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"
                else:
                    # Format: Month DD, YYYY
                    month = month_names.get(match.group(1), '01')
                    day = match.group(2).zfill(2)
                    year = match.group(3)
                    return f"{year}-{month}-{day}"
    
    return None

def fix_dates_in_database():
    """Fix date formats in the database"""
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Get all events with their current dates
    cursor.execute('SELECT id, date FROM events')
    events = cursor.fetchall()
    
    print(f"Found {len(events)} events to process")
    
    updated_count = 0
    for event_id, old_date in events:
        if old_date and not old_date.startswith('20'):  # Skip already formatted dates
            new_date = parse_date(old_date)
            if new_date:
                cursor.execute('UPDATE events SET date = ? WHERE id = ?', (new_date, event_id))
                updated_count += 1
                print(f"Updated event {event_id}: {old_date} -> {new_date}")
    
    conn.commit()
    conn.close()
    print(f"Updated {updated_count} events")

if __name__ == "__main__":
    fix_dates_in_database()










