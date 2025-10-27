#!/usr/bin/env python3
"""
Test script to verify calendar navigation and toggle fixes
"""

import requests
import time

def test_calendar_fixes():
    print("🧪 Testing Calendar Navigation and Toggle Fixes")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get('http://localhost:5001/', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running on http://localhost:5001")
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server with: python quick_start.py")
        return
    
    # Test 2: Check if events are loaded
    try:
        response = requests.get('http://localhost:5001/api/events', timeout=5)
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Events loaded: {len(events)} events")
        else:
            print(f"❌ Events API returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error loading events: {e}")
    
    # Test 3: Check if calendar endpoints work
    calendar_endpoints = ['/api/calendar/all', '/api/calendar/cs', '/api/calendar/biology']
    for endpoint in calendar_endpoints:
        try:
            response = requests.get(f'http://localhost:5001{endpoint}', timeout=5)
            if response.status_code == 200:
                print(f"✅ Calendar endpoint {endpoint} working")
            else:
                print(f"❌ Calendar endpoint {endpoint} returned {response.status_code}")
        except Exception as e:
            print(f"❌ Error with calendar endpoint {endpoint}: {e}")
    
    print("\n🎯 Manual Testing Instructions:")
    print("1. Open http://localhost:5001 in your browser")
    print("2. Open Developer Tools (F12) and go to Console tab")
    print("3. Test the following:")
    print("   - Click the left/right navigation arrows in the calendar")
    print("   - Click the 'Month' and 'Week' toggle buttons")
    print("   - Click on calendar events (should highlight events in left panel)")
    print("4. Look for these console messages:")
    print("   - 'Calendar navigation clicked: previous/next'")
    print("   - 'Calendar view toggle clicked: month/week'")
    print("   - 'Previous/Next month/week clicked'")
    print("   - 'Calendar event clicked: [event title]'")
    
    print("\n🔧 If buttons still don't work:")
    print("1. Check console for JavaScript errors")
    print("2. Verify the app object is available: type 'window.app' in console")
    print("3. Test manually: window.app.previousMonth() in console")
    print("4. Test manually: window.app.changeCalendarView('week') in console")

if __name__ == "__main__":
    test_calendar_fixes() 