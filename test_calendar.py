#!/usr/bin/env python3
"""
Test script for calendar functionality
"""

import requests
import tempfile
import os

def test_calendar_endpoints():
    """Test all calendar endpoints"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Calendar Endpoints...")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/calendar.ics", "All Events Calendar"),
        ("/api/calendar/all", "All Events (API)"),
        ("/api/calendar/cs", "Computer Science Events"),
        ("/api/calendar/biology", "Biology Events")
    ]
    
    for endpoint, description in endpoints:
        try:
            print(f"📅 Testing {description}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"   ✅ Success! Content length: {content_length} bytes")
                
                # Check if it's valid iCal content
                if b'BEGIN:VCALENDAR' in response.content and b'END:VCALENDAR' in response.content:
                    print(f"   ✅ Valid iCal format detected")
                else:
                    print(f"   ⚠️  Warning: May not be valid iCal format")
                    
            else:
                print(f"   ❌ Failed with status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")
        
        print()

def test_calendar_content():
    """Test calendar content structure"""
    print("🔍 Testing Calendar Content...")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:5001/calendar.ics", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for required iCal elements
            required_elements = [
                'BEGIN:VCALENDAR',
                'VERSION:2.0',
                'END:VCALENDAR'
            ]
            
            for element in required_elements:
                if element in content:
                    print(f"✅ Found: {element}")
                else:
                    print(f"❌ Missing: {element}")
            
            # Count events
            event_count = content.count('BEGIN:VEVENT')
            print(f"📊 Total events in calendar: {event_count}")
            
            # Show first few lines
            print("\n📄 First 10 lines of calendar file:")
            lines = content.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
                
        else:
            print(f"❌ Failed to get calendar content: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_calendar_endpoints()
    test_calendar_content() 