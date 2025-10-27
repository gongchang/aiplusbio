#!/usr/bin/env python3
"""
Performance test script for the AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area
"""

import time
import requests
import json

def test_loading_speed():
    """Test the loading speed of the application"""
    print("🚀 Testing application performance...")
    
    # Test API response time
    start_time = time.time()
    
    try:
        response = requests.get('http://localhost:5001/api/events', timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            events_count = len(data.get('events', []))
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            print(f"✅ API Response Time: {response_time:.2f}ms")
            print(f"📊 Events Loaded: {events_count}")
            print(f"📈 Performance: {events_count / (response_time / 1000):.1f} events/second")
            
            if response_time < 1000:
                print("🎉 Excellent performance!")
            elif response_time < 3000:
                print("👍 Good performance!")
            else:
                print("⚠️  Performance could be improved")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure the application is running on http://localhost:5001")

def test_filtering_speed():
    """Test filtering performance"""
    print("\n🔍 Testing filtering performance...")
    
    filters = [
        {'search': 'machine learning'},
        {'cs': 'true'},
        {'biology': 'true'},
        {'search': 'seminar', 'cs': 'true'}
    ]
    
    for filter_params in filters:
        start_time = time.time()
        
        try:
            params = '&'.join([f"{k}={v}" for k, v in filter_params.items()])
            response = requests.get(f'http://localhost:5001/api/events?{params}', timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                events_count = len(data.get('events', []))
                response_time = (end_time - start_time) * 1000
                
                filter_name = ' + '.join([f"{k}={v}" for k, v in filter_params.items()])
                print(f"✅ {filter_name}: {response_time:.2f}ms ({events_count} events)")
            else:
                print(f"❌ Filter test failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Filter test error: {e}")

if __name__ == '__main__':
    test_loading_speed()
    test_filtering_speed() 