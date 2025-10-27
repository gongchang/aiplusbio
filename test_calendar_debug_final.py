#!/usr/bin/env python3
"""
Final test to verify calendar fixes are working
"""

import requests
import json

def test_calendar_final():
    """Test final calendar functionality"""
    base_url = "http://localhost:5001"
    
    print("🧪 Final Calendar Test...")
    print("=" * 50)
    
    # Test 1: Check if main page loads with all required functions
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            
            # Check for required JavaScript functions
            required_functions = [
                'window.app = new EventsApp()',
                'setupCalendarEventListeners',
                'selectEventFromCalendar',
                'changeCalendarView',
                'previousMonth',
                'nextMonth',
                'previousWeek',
                'nextWeek'
            ]
            
            for func in required_functions:
                if func in response.text:
                    print(f"✅ Found: {func}")
                else:
                    print(f"❌ Missing: {func}")
                    
        else:
            print(f"❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check if events API works
    try:
        response = requests.get(f"{base_url}/api/events", timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"\n✅ API returns {len(events)} events")
            
            # Check if events have required fields
            if events:
                event = events[0]
                required_fields = ['id', 'title', 'date', 'categories']
                for field in required_fields:
                    if field in event:
                        print(f"✅ Event has {field}: {event[field]}")
                    else:
                        print(f"❌ Event missing {field}")
                        
        else:
            print(f"❌ API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎯 Manual Testing Instructions:")
    print("1. Open http://localhost:5001 in your browser")
    print("2. Open Developer Tools (F12) and go to Console tab")
    print("3. Refresh the page and look for these log messages:")
    print("   - 'EventsApp constructor called'")
    print("   - 'EventsApp init started'")
    print("   - 'Loaded X events'")
    print("   - 'Updating calendar with X events'")
    print("4. Test the calendar:")
    print("   - Click Month/Week toggle buttons")
    print("   - Click navigation arrows (previous/next)")
    print("   - Click on calendar events")
    print("5. Check if events highlight in left panel when clicked on calendar")

if __name__ == '__main__':
    test_calendar_final() 