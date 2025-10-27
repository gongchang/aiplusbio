#!/usr/bin/env python3
"""
Simple test to verify calendar functionality
"""

import requests
import json

def test_calendar_basic():
    """Test basic calendar functionality"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Calendar Basic Functionality...")
    print("=" * 50)
    
    # Test 1: Check if events are available
    try:
        response = requests.get(f"{base_url}/api/events", timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"✅ Found {len(events)} events")
            
            # Show first few events with dates
            print("\n📅 Sample events with dates:")
            for i, event in enumerate(events[:5]):
                print(f"   {i+1}. {event.get('title', 'No title')[:50]}...")
                print(f"      Date: {event.get('date', 'No date')}")
                print(f"      Categories: {event.get('categories', [])}")
                print()
        else:
            print(f"❌ Failed to get events: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check if calendar endpoints work
    try:
        response = requests.get(f"{base_url}/calendar.ics", timeout=10)
        if response.status_code == 200:
            print(f"✅ Calendar ICS endpoint works ({len(response.content)} bytes)")
        else:
            print(f"❌ Calendar ICS endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check if main page loads
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            
            # Check if calendar container is present
            if 'calendarContainer' in response.text:
                print("✅ Calendar container found in HTML")
            else:
                print("❌ Calendar container not found in HTML")
        else:
            print(f"❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_calendar_basic() 