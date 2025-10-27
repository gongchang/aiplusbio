#!/usr/bin/env python3
"""
Test to verify calendar fixes are working
"""

import requests
import json

def test_calendar_fixes():
    """Test calendar functionality fixes"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Calendar Fixes...")
    print("=" * 50)
    
    # Test 1: Check if events have proper IDs
    try:
        response = requests.get(f"{base_url}/api/events", timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            print(f"✅ Found {len(events)} events")
            
            # Check if events have IDs
            events_with_ids = [e for e in events if 'id' in e]
            print(f"✅ {len(events_with_ids)} events have IDs")
            
            # Show sample events with IDs
            print("\n📅 Sample events with IDs:")
            for i, event in enumerate(events[:3]):
                print(f"   {i+1}. ID: {event.get('id', 'No ID')} | {event.get('title', 'No title')[:40]}...")
                print(f"      Date: {event.get('date', 'No date')}")
                print()
                
        else:
            print(f"❌ Failed to get events: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check if main page loads with calendar
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            
            # Check for calendar elements
            if 'calendarContainer' in response.text:
                print("✅ Calendar container found")
            if 'changeCalendarView' in response.text:
                print("✅ Calendar view toggle functions found")
            if 'previousMonth' in response.text:
                print("✅ Calendar navigation functions found")
            if 'selectEventFromCalendar' in response.text:
                print("✅ Calendar event selection functions found")
                
        else:
            print(f"❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎯 Manual Testing Required:")
    print("1. Open http://localhost:5001 in your browser")
    print("2. Test Month/Week toggle buttons")
    print("3. Test navigation arrows (previous/next)")
    print("4. Click on calendar events to see if they highlight in left panel")
    print("5. Check browser console for any JavaScript errors")

if __name__ == '__main__':
    test_calendar_fixes() 