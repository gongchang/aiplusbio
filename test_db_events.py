#!/usr/bin/env python3

from database import Database
from datetime import datetime

def test_database():
    db = Database()
    
    # Get all events
    all_events = db.get_events()
    print(f"Total events returned by get_events(): {len(all_events)}")
    
    # Check dates
    today = datetime.now().date()
    print(f"Today's date: {today}")
    
    # Count events by date range
    future_events = [e for e in all_events if e['date'] >= today.isoformat()]
    past_events = [e for e in all_events if e['date'] < today.isoformat()]
    
    print(f"Future events (>= today): {len(future_events)}")
    print(f"Past events (< today): {len(past_events)}")
    
    # Show some sample events
    print("\nSample events:")
    for i, event in enumerate(all_events[:5]):
        print(f"{i+1}. {event['title'][:50]}... | Date: {event['date']} | Source: {event['source_url']}")
    
    # Check IAIFI events specifically
    iaifi_events = [e for e in all_events if 'iaifi' in e['source_url'].lower()]
    print(f"\nIAIFI events: {len(iaifi_events)}")
    for event in iaifi_events[:3]:
        print(f"- {event['title'][:50]}... | Date: {event['date']}")
    
    # Check Schmidt events specifically
    schmidt_events = [e for e in all_events if 'schmidt' in e['source_url'].lower()]
    print(f"\nSchmidt events: {len(schmidt_events)}")
    for event in schmidt_events:
        print(f"- {event['title'][:50]}... | Date: {event['date']}")

if __name__ == "__main__":
    test_database()










