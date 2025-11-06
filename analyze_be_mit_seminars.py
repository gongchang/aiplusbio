#!/usr/bin/env python3
"""
Detailed analysis of BE MIT Seminars site to understand the JavaScript issue
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time

def analyze_be_mit_seminars():
    """Detailed analysis of BE MIT Seminars site"""
    print("🔍 Detailed Analysis: BE MIT Seminars")
    print("=" * 60)
    
    url = "https://be.mit.edu/our-community/seminars/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"📡 Fetching: {url}")
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Content Length: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n🏗️  HTML Structure Analysis:")
        print("-" * 40)
        
        # Check for JavaScript files
        scripts = soup.find_all('script')
        print(f"📜 JavaScript files found: {len(scripts)}")
        
        js_files = []
        for script in scripts:
            src = script.get('src', '')
            if src:
                js_files.append(src)
            elif script.string:
                # Check for inline JavaScript
                js_content = script.string.lower()
                if 'event' in js_content or 'seminar' in js_content or 'calendar' in js_content:
                    print(f"  ⚠️  Found inline JavaScript with event-related content")
        
        if js_files:
            print("  📜 External JavaScript files:")
            for js in js_files[:5]:  # Show first 5
                print(f"    • {js}")
        
        # Check for AJAX endpoints or API calls
        print(f"\n🔌 Potential AJAX/API Endpoints:")
        print("-" * 40)
        
        # Look for common API patterns in JavaScript
        js_content = soup.get_text()
        api_patterns = [
            r'fetch\([\'"]([^\'"]*api[^\'"]*)[\'"]',
            r'\.ajax\([\'"]([^\'"]*)[\'"]',
            r'axios\.get\([\'"]([^\'"]*)[\'"]',
            r'url:\s*[\'"]([^\'"]*)[\'"]',
            r'endpoint:\s*[\'"]([^\'"]*)[\'"]'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, js_content, re.I)
            if matches:
                print(f"  🔗 Found potential API endpoints:")
                for match in matches[:3]:  # Show first 3
                    print(f"    • {match}")
        
        # Check for data attributes that might contain event info
        print(f"\n📊 Data Attributes Analysis:")
        print("-" * 40)
        
        data_elements = soup.find_all(attrs={"data-": True})
        print(f"  📋 Elements with data attributes: {len(data_elements)}")
        
        for elem in data_elements[:5]:  # Show first 5
            attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
            if attrs:
                print(f"    • {elem.name}: {attrs}")
        
        # Check for calendar/seminar specific elements
        print(f"\n📅 Calendar/Seminar Elements:")
        print("-" * 40)
        
        calendar_selectors = [
            'div[class*="calendar"]',
            'div[class*="seminar"]',
            'div[class*="event"]',
            'div[class*="schedule"]',
            'table[class*="calendar"]',
            'table[class*="seminar"]'
        ]
        
        for selector in calendar_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"  ✅ Found {len(elements)} elements with selector: {selector}")
                for elem in elements[:2]:  # Show first 2
                    print(f"    • Class: {elem.get('class', 'No class')}")
                    print(f"    • Text preview: {elem.get_text()[:100]}...")
        
        # Check for iframes
        iframes = soup.find_all('iframe')
        if iframes:
            print(f"\n🖼️  Iframes found: {len(iframes)}")
            for iframe in iframes:
                src = iframe.get('src', 'No src')
                print(f"  • {src}")
        
        # Check for loading states or placeholders
        print(f"\n⏳ Loading States/Placeholders:")
        print("-" * 40)
        
        loading_indicators = [
            'loading', 'spinner', 'placeholder', 'skeleton', 'shimmer'
        ]
        
        for indicator in loading_indicators:
            elements = soup.find_all(class_=re.compile(indicator, re.I))
            if elements:
                print(f"  ⏳ Found {len(elements)} elements with '{indicator}' class")
        
        # Check for dynamic content containers
        print(f"\n🔄 Dynamic Content Analysis:")
        print("-" * 40)
        
        dynamic_containers = soup.find_all(id=re.compile(r'(content|main|app|root)', re.I))
        print(f"  📦 Main content containers: {len(dynamic_containers)}")
        
        for container in dynamic_containers:
            print(f"    • ID: {container.get('id')}")
            print(f"    • Content length: {len(container.get_text())} chars")
            print(f"    • Has children: {len(container.find_all())} elements")
        
        # Check for React/Vue/Angular indicators
        print(f"\n⚛️  JavaScript Framework Indicators:")
        print("-" * 40)
        
        framework_indicators = {
            'React': ['react', 'jsx', 'data-react'],
            'Vue': ['vue', 'v-', 'data-vue'],
            'Angular': ['ng-', 'data-ng', 'angular'],
            'jQuery': ['jquery', '$('],
            'Backbone': ['backbone', 'data-backbone']
        }
        
        for framework, indicators in framework_indicators.items():
            for indicator in indicators:
                if indicator in js_content.lower():
                    print(f"  ⚛️  Potential {framework} usage detected")
                    break
        
        # Check for event listeners or DOM manipulation
        print(f"\n🎯 Event Listeners/DOM Manipulation:")
        print("-" * 40)
        
        dom_patterns = [
            r'addEventListener',
            r'\.on\([\'"]',
            r'document\.getElementById',
            r'querySelector',
            r'innerHTML',
            r'appendChild'
        ]
        
        for pattern in dom_patterns:
            matches = re.findall(pattern, js_content, re.I)
            if matches:
                print(f"  🎯 Found {len(matches)} instances of: {pattern}")
        
        print(f"\n🎯 Summary:")
        print("=" * 60)
        print("The BE MIT Seminars site likely uses JavaScript to:")
        print("1. Load event data dynamically via AJAX/API calls")
        print("2. Render calendar/seminar content after page load")
        print("3. Handle user interactions and filtering")
        print("4. Manage state and data updates")
        print("\nTo fix this, we would need:")
        print("• JavaScript rendering (Selenium/Playwright)")
        print("• API endpoint discovery and direct access")
        print("• Wait for dynamic content to load")
        print("• Handle authentication if required")
        
    except Exception as e:
        print(f"❌ Error analyzing site: {e}")

def test_potential_api_endpoints():
    """Test potential API endpoints for event data"""
    print(f"\n🔌 Testing Potential API Endpoints")
    print("=" * 60)
    
    potential_endpoints = [
        "https://be.mit.edu/api/events",
        "https://be.mit.edu/api/seminars", 
        "https://be.mit.edu/events.json",
        "https://be.mit.edu/seminars.json",
        "https://be.mit.edu/wp-json/wp/v2/posts",
        "https://be.mit.edu/wp-json/wp/v2/events"
    ]
    
    for endpoint in potential_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"🔗 {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Found working endpoint!")
                try:
                    data = response.json()
                    print(f"  📊 Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"  📋 Items: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"  📋 Keys: {list(data.keys())[:5]}")
                except:
                    print(f"  📄 Response is not JSON")
        except Exception as e:
            print(f"🔗 {endpoint}: Error - {e}")

def main():
    """Main analysis function"""
    analyze_be_mit_seminars()
    test_potential_api_endpoints()

if __name__ == "__main__":
    main()











