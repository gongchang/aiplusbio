#!/usr/bin/env python3
"""
Test script to verify AI+Bio Events Aggregator setup
"""

import sys
import os
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError:
        print("❌ Flask import failed")
        return False
    
    try:
        import requests
        print("✅ Requests imported successfully")
    except ImportError:
        print("❌ Requests import failed")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup imported successfully")
    except ImportError:
        print("❌ BeautifulSoup import failed")
        return False
    
    try:
        import openai
        print("✅ OpenAI imported successfully")
    except ImportError:
        print("❌ OpenAI import failed")
        return False
    
    try:
        import sqlite3
        print("✅ SQLite3 imported successfully")
    except ImportError:
        print("❌ SQLite3 import failed")
        return False
    
    return True

def test_local_modules():
    """Test if local modules can be imported"""
    print("\n🔍 Testing local modules...")
    
    try:
        from database import Database
        print("✅ Database module imported successfully")
    except ImportError as e:
        print(f"❌ Database module import failed: {e}")
        return False
    
    try:
        from event_scraper import EventScraper
        print("✅ EventScraper module imported successfully")
    except ImportError as e:
        print(f"❌ EventScraper module import failed: {e}")
        return False
    
    try:
        from event_categorizer import EventCategorizer
        print("✅ EventCategorizer module imported successfully")
    except ImportError as e:
        print(f"❌ EventCategorizer module import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\n🔍 Testing database...")
    
    try:
        from database import Database
        db = Database('test.db')
        db.init_db()
        print("✅ Database initialization successful")
        
        # Test adding an event
        test_event = {
            'title': 'Test Event',
            'description': 'This is a test event',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': '10:00 AM',
            'location': 'Test Location',
            'url': 'https://example.com',
            'source_url': 'https://example.com',
            'is_virtual': False,
            'requires_registration': False,
            'categories': []
        }
        
        event_id = db.add_event(test_event)
        print(f"✅ Event added successfully with ID: {event_id}")
        
        # Test retrieving events
        events = db.get_events()
        print(f"✅ Retrieved {len(events)} events from database")
        
        # Cleanup test database
        os.remove('test.db')
        print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_websites_file():
    """Test if websites file exists and is readable"""
    print("\n🔍 Testing websites file...")
    
    if not os.path.exists('websites_to_watch.txt'):
        print("❌ websites_to_watch.txt not found")
        return False
    
    try:
        with open('websites_to_watch.txt', 'r') as f:
            websites = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"✅ Found {len(websites)} websites to monitor")
        for website in websites[:3]:  # Show first 3
            print(f"   - {website}")
        if len(websites) > 3:
            print(f"   ... and {len(websites) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading websites file: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found (will use default settings)")
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != 'your_openai_api_key_here':
        print("✅ OpenAI API key configured")
    else:
        print("⚠️  OpenAI API key not configured (will use keyword matching)")
    
    return True

def main():
    """Run all tests"""
    print("🧪 AI+Bio Events Aggregator - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_local_modules,
        test_database,
        test_websites_file,
        test_environment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\n🚀 To start the application, run:")
        print("   python run.py")
        print("   or")
        print("   python app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Common solutions:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Check if all files are in the correct location")
        print("   3. Verify Python version (3.8+)")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 