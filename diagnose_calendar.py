#!/usr/bin/env python3
"""
Diagnostic script to check calendar functionality
"""

import requests
import json
import time

def diagnose_calendar():
    print("🔍 Calendar Diagnosis")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test 2: Check events API
    try:
        response = requests.get(f"{base_url}/api/events", timeout=5)
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Events API working: {len(events)} events")
            
            # Check if events have dates
            events_with_dates = [e for e in events if e.get('date')]
            print(f"   - Events with dates: {len(events_with_dates)}")
            
            # Show sample event
            if events:
                sample = events[0]
                print(f"   - Sample event: {sample.get('title', 'No title')} on {sample.get('date', 'No date')}")
        else:
            print(f"❌ Events API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Events API error: {e}")
    
    # Test 3: Check calendar endpoints
    calendar_endpoints = [
        "/api/calendar/all",
        "/api/calendar/cs", 
        "/api/calendar/biology"
    ]
    
    for endpoint in calendar_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Calendar endpoint {endpoint} working")
                # Check if it returns valid iCal content
                content = response.text
                if content.startswith("BEGIN:VCALENDAR"):
                    print(f"   - Returns valid iCal format ({len(content)} chars)")
                else:
                    print(f"   - Returns non-iCal format ({len(content)} chars)")
            else:
                print(f"❌ Calendar endpoint {endpoint} returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Calendar endpoint {endpoint} error: {e}")
    
    # Test 4: Check static files
    static_files = [
        "/static/js/app.js",
        "/static/css/style.css"
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(f"{base_url}{file_path}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Static file {file_path} accessible")
            else:
                print(f"❌ Static file {file_path} returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Static file {file_path} error: {e}")
    
    print("\n🎯 Manual Testing Instructions:")
    print("1. Open http://localhost:5001 in your browser")
    print("2. Open Developer Tools (F12) → Console")
    print("3. Run this JavaScript to test calendar functions:")
    print("""
    // Test if app is available
    console.log('App available:', typeof window.app !== 'undefined');
    
    if (window.app) {
        console.log('App state:', {
            events: window.app.events.length,
            calendarView: window.app.calendarView,
            currentDate: window.app.currentDate
        });
        
        // Test view change
        window.app.changeCalendarView('week');
        console.log('Changed to week view');
        
        // Test navigation
        window.app.nextMonth();
        console.log('Navigated to next month');
    }
    """)
    
    print("\n🔧 If calendar still doesn't work:")
    print("1. Check browser console for JavaScript errors")
    print("2. Verify the app object exists: window.app")
    print("3. Check if calendar container exists: document.getElementById('calendarContainer')")
    print("4. Try the standalone test page: force_calendar_test.html")

if __name__ == "__main__":
    diagnose_calendar() 