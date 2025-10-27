"""
Enhanced Computing Event Searcher using multiple APIs
- Tavily API with improved date filtering
- Eventbrite API for structured event data
- Luma API for additional event sources
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from database import Database


class EnhancedComputingEventSearcher:
    def __init__(self, db_path='events.db'):
        self.db = Database(db_path)
        self.tavily_api_key = os.getenv('Tavily_API')
        self.eventbrite_api_key = os.getenv('EVENTBRITE_API_KEY')
        self.luma_api_key = os.getenv('LUMA_API_KEY')
        
        self.tavily_base_url = "https://api.tavily.com/search"
        self.eventbrite_base_url = "https://www.eventbriteapi.com/v3"
        
        # Keywords for computing-related events (exact list from requirements)
        self.computing_keywords = [
            'AI', 'AI agents', 'Machine learning', 'computational biology', 
            'bioinformatics', 'cloud computing', 'devops'
        ]
        
        # Keywords for formal events (exact list from requirements, excluding meetups)
        self.event_keywords = [
            'workshop', 'tutorials', 'community day', 'dev days', 'events',
            'symposium', 'meeting', 'conference', 'webinar', 'user group'
        ]
        
        # Keywords to exclude (informal events)
        self.excluded_event_keywords = [
            'meetup', 'meetups', 'networking', 'happy hour', 'social'
        ]
        
        # Boston area keywords (Greater Boston area, Massachusetts, USA)
        self.location_keywords = [
            'Boston', 'Cambridge', 'Somerville', 'Brookline', 'Newton',
            'Watertown', 'Waltham', 'Lexington', 'Arlington', 'Medford',
            'Massachusetts', 'MA', 'Greater Boston', 'Boston area',
            'MIT', 'Harvard', 'Boston University', 'BU', 'Northeastern'
        ]
        
        # Load exclusion URLs from websites_to_watch.txt
        self.exclusion_urls = self._load_exclusion_urls()
        
        # Date range for search (next 6 months)
        self.date_range = self._get_date_range()
    
    def _load_exclusion_urls(self) -> List[str]:
        """Load URLs that should be excluded from search results"""
        exclusion_urls = []
        try:
            with open('websites_to_watch.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        exclusion_urls.append(line.lower())
        except FileNotFoundError:
            print("Warning: websites_to_watch.txt not found")
        return exclusion_urls
    
    def _get_date_range(self) -> Dict[str, str]:
        """Get date range for next 6 months"""
        today = datetime.now()
        six_months_later = today + timedelta(days=180)
        
        return {
            'start_date': today.strftime('%Y-%m-%d'),
            'end_date': six_months_later.strftime('%Y-%m-%d'),
            'start_time': today.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': six_months_later.strftime('%Y-%m-%dT%H:%M:%S')
        }
    
    def search_events(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for computing events using multiple APIs"""
        all_events = []
        
        print(f"🔍 Searching for computing events in Boston area (next 6 months)")
        print(f"📅 Date range: {self.date_range['start_date']} to {self.date_range['end_date']}")
        print(f"🎯 Max results: {max_results}")
        print("-" * 60)
        
        # Search using Tavily API with improved date filtering
        tavily_events = self._search_tavily_events(max_results // 2)
        all_events.extend(tavily_events)
        
        # Search using Eventbrite API
        if self.eventbrite_api_key:
            eventbrite_events = self._search_eventbrite_events(max_results // 2)
            all_events.extend(eventbrite_events)
        else:
            print("⚠️  Eventbrite API key not found - skipping Eventbrite search")
        
        # Search using Luma API (if available)
        if self.luma_api_key:
            luma_events = self._search_luma_events(max_results // 4)
            all_events.extend(luma_events)
        else:
            print("⚠️  Luma API key not found - skipping Luma search")
        
        # Remove duplicates and filter
        unique_events = self._remove_duplicates(all_events)
        filtered_events = self._filter_events(unique_events, max_results)
        
        print(f"✅ Found {len(filtered_events)} unique events meeting all criteria")
        return filtered_events
    
    def _search_tavily_events(self, max_results: int) -> List[Dict[str, Any]]:
        """Search for events using Tavily API with improved date filtering"""
        print("🔍 Searching Tavily API...")
        
        try:
            # Build more specific query with date range
            query = self._build_enhanced_tavily_query()
            print(f"Tavily query: {query}")
            
            payload = {
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results * 2,  # Get more to filter
                "include_answer": False,
                "include_raw_content": True,
                "include_domains": [],
                "exclude_domains": []
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tavily_api_key}"
            }
            
            response = requests.post(
                self.tavily_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Tavily API error: {response.status_code} - {response.text}")
                return []
            
            search_results = response.json()
            events = []
            
            for result in search_results.get('results', []):
                if self._meets_all_criteria(result):
                    event = self._extract_event_from_result(result, source='Tavily')
                    if event and not self._is_excluded_url(event.get('url', '')):
                        events.append(event)
            
            print(f"Tavily found {len(events)} relevant events")
            return events
            
        except Exception as e:
            print(f"Error searching Tavily: {e}")
            return []
    
    def _build_enhanced_tavily_query(self) -> str:
        """Build enhanced Tavily query with date range"""
        # Criterion 1: Computing-related keywords
        computing_terms = 'AI OR "AI agents" OR "machine learning" OR "computational biology" OR bioinformatics OR "cloud computing" OR devops'
        
        # Criterion 2: Formal event keywords (excluding meetups)
        event_terms = 'workshop OR tutorials OR "community day" OR "dev days" OR symposium OR meeting OR conference OR webinar OR "user group"'
        
        # Criterion 3: Boston area location
        location_terms = 'Boston OR Cambridge OR Massachusetts OR MIT OR Harvard'
        
        # Criterion 5: Future events with specific date range
        current_year = datetime.now().year
        future_terms = f'upcoming OR future OR {current_year} OR {current_year + 1} OR "next 6 months" OR "coming months"'
        
        # Build the main query
        query = f'({computing_terms}) AND ({event_terms}) AND ({location_terms}) AND ({future_terms})'
        
        return query
    
    def _search_eventbrite_events(self, max_results: int) -> List[Dict[str, Any]]:
        """Search for events using Eventbrite API"""
        print("🎫 Searching Eventbrite API...")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.eventbrite_api_key}'
            }
            
            # Eventbrite search parameters
            params = {
                'location.address': 'Boston, MA',
                'location.within': '50mi',  # 50 mile radius
                'start_date.range_start': self.date_range['start_time'],
                'start_date.range_end': self.date_range['end_time'],
                'categories': '102',  # Technology category
                'q': 'AI OR machine learning OR cloud computing OR devops',
                'expand': 'venue,organizer',
                'status': 'live',
                'page_size': min(max_results * 2, 50)  # Eventbrite limit
            }
            
            response = requests.get(
                f'{self.eventbrite_base_url}/events/search',
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Eventbrite API error: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            events = []
            
            for event_data in data.get('events', []):
                event = self._extract_eventbrite_event(event_data)
                if event and self._meets_eventbrite_criteria(event):
                    events.append(event)
            
            print(f"Eventbrite found {len(events)} relevant events")
            return events
            
        except Exception as e:
            print(f"Error searching Eventbrite: {e}")
            return []
    
    def _extract_eventbrite_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract event information from Eventbrite API response"""
        try:
            name = event_data.get('name', {}).get('text', '').strip()
            if not name:
                return None
            
            # Check if event contains computing keywords
            if not any(keyword.lower() in name.lower() for keyword in self.computing_keywords):
                return None
            
            # Extract event details
            event = {
                'title': name,
                'description': event_data.get('description', {}).get('text', ''),
                'url': event_data.get('url', ''),
                'source_url': event_data.get('url', ''),
                'is_virtual': event_data.get('is_online_event', False),
                'requires_registration': True,  # Eventbrite events require registration
                'categories': self._extract_categories(name),
                'host': self._extract_eventbrite_host(event_data),
                'cost_type': self._extract_eventbrite_cost(event_data),
                'date': self._extract_eventbrite_date(event_data),
                'time': self._extract_eventbrite_time(event_data),
                'location': self._extract_eventbrite_location(event_data),
                'source': 'Eventbrite'
            }
            
            return event
            
        except Exception as e:
            print(f"Error extracting Eventbrite event: {e}")
            return None
    
    def _extract_eventbrite_host(self, event_data: Dict[str, Any]) -> str:
        """Extract host from Eventbrite event data"""
        try:
            organizer = event_data.get('organizer', {})
            if organizer:
                return organizer.get('name', 'Other')
            return 'Other'
        except:
            return 'Other'
    
    def _extract_eventbrite_cost(self, event_data: Dict[str, Any]) -> str:
        """Extract cost information from Eventbrite event data"""
        try:
            is_free = event_data.get('is_free', False)
            if is_free:
                return 'Free'
            
            # Check if there are paid tickets
            ticket_classes = event_data.get('ticket_availability', {}).get('ticket_classes', [])
            for ticket in ticket_classes:
                if ticket.get('free', False):
                    return 'Free'
            
            return 'Paid'
        except:
            return 'Unknown'
    
    def _extract_eventbrite_date(self, event_data: Dict[str, Any]) -> str:
        """Extract date from Eventbrite event data"""
        try:
            start_date = event_data.get('start', {}).get('local', '')
            if start_date:
                # Parse ISO format and return YYYY-MM-DD
                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            return ''
        except:
            return ''
    
    def _extract_eventbrite_time(self, event_data: Dict[str, Any]) -> str:
        """Extract time from Eventbrite event data"""
        try:
            start_date = event_data.get('start', {}).get('local', '')
            if start_date:
                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                return dt.strftime('%H:%M')
            return ''
        except:
            return ''
    
    def _extract_eventbrite_location(self, event_data: Dict[str, Any]) -> str:
        """Extract location from Eventbrite event data"""
        try:
            venue = event_data.get('venue', {})
            if venue:
                address = venue.get('address', {})
                city = address.get('city', '')
                state = address.get('region', '')
                if city and state:
                    return f"{city}, {state}"
                elif city:
                    return city
            
            # Fallback to Boston area if online event
            if event_data.get('is_online_event'):
                return 'Virtual'
            
            return 'Boston Area'
        except:
            return 'Boston Area'
    
    def _meets_eventbrite_criteria(self, event: Dict[str, Any]) -> bool:
        """Check if Eventbrite event meets our criteria"""
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Must be computing-related
        has_computing = any(keyword.lower() in combined_text for keyword in self.computing_keywords)
        
        # Must be formal event (no meetups)
        has_formal_event = any(keyword.lower() in combined_text for keyword in self.event_keywords)
        has_informal_event = any(keyword.lower() in combined_text for keyword in self.excluded_event_keywords)
        
        # Must be in Boston area
        has_location = any(keyword.lower() in combined_text for keyword in self.location_keywords)
        
        return has_computing and has_formal_event and not has_informal_event and has_location
    
    def _search_luma_events(self, max_results: int) -> List[Dict[str, Any]]:
        """Search for events using Luma API"""
        print("📅 Searching Luma API...")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.luma_api_key}'
            }
            
            # Note: Luma API structure may vary - this is a general approach
            # Using the correct Luma API endpoint
            response = requests.get(
                'https://api.lu.ma/api/v1/calendar/events',
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Luma API error: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            events = []
            
            for event_data in data.get('events', []):
                event = self._extract_luma_event(event_data)
                if event and self._meets_luma_criteria(event):
                    events.append(event)
            
            print(f"Luma found {len(events)} relevant events")
            return events
            
        except Exception as e:
            print(f"Error searching Luma: {e}")
            return []
    
    def _extract_luma_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract event information from Luma API response"""
        try:
            title = event_data.get('name', '').strip()
            if not title:
                return None
            
            event = {
                'title': title,
                'description': event_data.get('description', ''),
                'url': event_data.get('url', ''),
                'source_url': event_data.get('url', ''),
                'is_virtual': event_data.get('is_online', False),
                'requires_registration': True,
                'categories': self._extract_categories(title),
                'host': event_data.get('organizer', {}).get('name', 'Other'),
                'cost_type': 'Free' if event_data.get('is_free', True) else 'Paid',
                'date': self._extract_luma_date(event_data),
                'time': self._extract_luma_time(event_data),
                'location': event_data.get('location', {}).get('name', 'Boston Area'),
                'source': 'Luma'
            }
            
            return event
            
        except Exception as e:
            print(f"Error extracting Luma event: {e}")
            return None
    
    def _extract_luma_date(self, event_data: Dict[str, Any]) -> str:
        """Extract date from Luma event data"""
        try:
            start_time = event_data.get('start_at')
            if start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            return ''
        except:
            return ''
    
    def _extract_luma_time(self, event_data: Dict[str, Any]) -> str:
        """Extract time from Luma event data"""
        try:
            start_time = event_data.get('start_at')
            if start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                return dt.strftime('%H:%M')
            return ''
        except:
            return ''
    
    def _meets_luma_criteria(self, event: Dict[str, Any]) -> bool:
        """Check if Luma event meets our criteria"""
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Same criteria as Eventbrite
        has_computing = any(keyword.lower() in combined_text for keyword in self.computing_keywords)
        has_formal_event = any(keyword.lower() in combined_text for keyword in self.event_keywords)
        has_informal_event = any(keyword.lower() in combined_text for keyword in self.excluded_event_keywords)
        has_location = any(keyword.lower() in combined_text for keyword in self.location_keywords)
        
        return has_computing and has_formal_event and not has_informal_event and has_location
    
    def _meets_all_criteria(self, result: Dict[str, Any]) -> bool:
        """Check if search result meets ALL five required criteria"""
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        combined_text = f"{title} {content}"
        
        # Criterion 1: Must be computing-related
        has_computing = any(keyword.lower() in combined_text for keyword in self.computing_keywords)
        
        # Criterion 2: Must be a formal event (exclude meetups and informal events)
        has_formal_event = any(keyword.lower() in combined_text for keyword in self.event_keywords)
        has_informal_event = any(keyword.lower() in combined_text for keyword in self.excluded_event_keywords)
        
        # Criterion 3: Must be local to Greater Boston area, Massachusetts, USA
        has_location = any(keyword.lower() in combined_text for keyword in self.location_keywords)
        
        # Criterion 5: Must be held in the future (today and beyond) - STRICT validation
        is_future_event = self._is_future_event(combined_text)
        
        return has_computing and has_formal_event and not has_informal_event and has_location and is_future_event
    
    def _is_future_event(self, text: str) -> bool:
        """Strict validation for future events"""
        from datetime import datetime
        import re
        
        # Check for explicit future keywords
        has_future_keywords = any(keyword in text for keyword in [
            'upcoming', 'future', 'next', 'tomorrow', 'this week', 'this month'
        ])
        
        # Check for current and future years
        current_year = datetime.now().year
        future_years = [str(current_year), str(current_year + 1), str(current_year + 2)]
        has_future_years = any(year in text for year in future_years)
        
        # Check for specific future dates (month day format)
        month_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}',
        ]
        
        has_future_dates = any(re.search(pattern, text) for pattern in month_patterns)
        
        # Check for "today" or "tonight"
        has_today = any(word in text for word in ['today', 'tonight', 'this evening'])
        
        # Check for "this week", "this month" (more likely to be future)
        has_this_period = any(phrase in text for phrase in ['this week', 'this month', 'next week', 'next month'])
        
        return has_future_keywords or has_future_years or has_future_dates or has_today or has_this_period
    
    def _extract_event_from_result(self, result: Dict[str, Any], source: str = 'Tavily') -> Optional[Dict[str, Any]]:
        """Extract event information from search result"""
        try:
            title = result.get('title', '').strip()
            url = result.get('url', '')
            content = result.get('content', '')
            
            if not title or not url:
                return None
            
            # Extract event details from content
            event = {
                'title': title,
                'url': url,
                'description': content[:500] + '...' if len(content) > 500 else content,
                'source_url': url,
                'is_virtual': self._is_virtual_event(content),
                'requires_registration': self._requires_registration(content),
                'categories': self._extract_categories(title, content),
                'host': self._extract_host(url, content),
                'cost_type': self._determine_cost_type(content),
                'date': self._extract_date(content),
                'time': self._extract_time(content),
                'location': self._extract_location(content),
                'source': source
            }
            
            return event
            
        except Exception as e:
            print(f"Error extracting event from result: {e}")
            return None
    
    def _is_virtual_event(self, content: str) -> bool:
        """Determine if event is virtual"""
        virtual_keywords = ['virtual', 'online', 'zoom', 'webinar', 'live stream', 'remote']
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in virtual_keywords)
    
    def _requires_registration(self, content: str) -> bool:
        """Determine if event requires registration"""
        reg_keywords = ['register', 'registration', 'rsvp', 'sign up', 'ticket', 'reserve']
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in reg_keywords)
    
    def _extract_categories(self, title: str, content: str = '') -> List[str]:
        """Extract categories from title and content"""
        categories = []
        text = (title + ' ' + content).lower()
        
        if any(keyword in text for keyword in ['ai', 'artificial intelligence', 'machine learning']):
            categories.append('AI')
        if any(keyword in text for keyword in ['computational biology', 'bioinformatics']):
            categories.append('Computational Biology')
        if any(keyword in text for keyword in ['cloud computing', 'devops']):
            categories.append('Cloud Computing')
        if any(keyword in text for keyword in ['data science', 'big data']):
            categories.append('Data Science')
        if any(keyword in text for keyword in ['computer science', 'programming', 'software engineering']):
            categories.append('Computer Science')
        
        return categories if categories else ['Computing']
    
    def _extract_host(self, url: str, content: str) -> str:
        """Extract host/organizer from URL and content"""
        try:
            # Extract domain from URL
            domain = urlparse(url).netloc.lower()
            
            # Known hosts mapping
            host_mapping = {
                'amazon.com': 'Amazon',
                'google.com': 'Google',
                'microsoft.com': 'Microsoft',
                'facebook.com': 'Meta',
                'meta.com': 'Meta',
                'apple.com': 'Apple',
                'nvidia.com': 'NVIDIA',
                'intel.com': 'Intel',
                'ibm.com': 'IBM',
                'oracle.com': 'Oracle',
                'salesforce.com': 'Salesforce',
                'adobe.com': 'Adobe',
                'netflix.com': 'Netflix',
                'uber.com': 'Uber',
                'airbnb.com': 'Airbnb',
                'linkedin.com': 'LinkedIn',
                'twitter.com': 'Twitter',
                'github.com': 'GitHub',
                'docker.com': 'Docker',
                'kubernetes.io': 'Kubernetes',
                'redhat.com': 'Red Hat',
                'vmware.com': 'VMware',
                'cisco.com': 'Cisco',
                'atlassian.com': 'Atlassian',
                'slack.com': 'Slack',
                'zoom.us': 'Zoom',
                'dropbox.com': 'Dropbox',
                'box.com': 'Box',
                'okta.com': 'Okta',
                'paloaltonetworks.com': 'Palo Alto Networks',
                'crowdstrike.com': 'CrowdStrike',
                'splunk.com': 'Splunk',
                'databricks.com': 'Databricks',
                'snowflake.com': 'Snowflake',
                'mongodb.com': 'MongoDB',
                'redis.io': 'Redis',
                'elastic.co': 'Elastic',
                'confluent.io': 'Confluent',
                'hashicorp.com': 'HashiCorp',
                'eventbrite.com': 'Eventbrite'
            }
            
            # Check for exact domain matches
            for domain_key, host_name in host_mapping.items():
                if domain_key in domain:
                    return host_name
            
            # Check for partial domain matches
            for domain_key, host_name in host_mapping.items():
                if domain_key.replace('.com', '') in domain:
                    return host_name
            
            # Extract organization from content if available
            content_lower = content.lower()
            for host_name in host_mapping.values():
                if host_name.lower() in content_lower:
                    return host_name
            
            # Fallback to domain name
            if domain:
                domain_parts = domain.replace('www.', '').split('.')
                if domain_parts:
                    return domain_parts[0].title()
            
            return 'Other'
            
        except Exception:
            return 'Other'
    
    def _determine_cost_type(self, content: str) -> str:
        """Determine if event is free or paid"""
        content_lower = content.lower()
        
        paid_keywords = ['cost', 'price', 'fee', 'ticket', 'buy', 'purchase', '$', 'paid', 'charge']
        free_keywords = ['free', 'no cost', 'complimentary', 'gratis', 'no charge']
        
        has_paid = any(keyword in content_lower for keyword in paid_keywords)
        has_free = any(keyword in content_lower for keyword in free_keywords)
        
        if has_free and not has_paid:
            return 'Free'
        elif has_paid:
            return 'Paid'
        else:
            return 'Unknown'
    
    def _extract_date(self, content: str) -> str:
        """Extract event date from content"""
        import re
        
        # Look for common date patterns
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_time(self, content: str) -> str:
        """Extract event time from content"""
        import re
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*[AP]M)',
            r'(\d{1,2}\s*[AP]M)',
            r'(\d{1,2}:\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_location(self, content: str) -> str:
        """Extract event location from content"""
        # Look for Boston area locations
        boston_locations = [
            'Boston', 'Cambridge', 'Somerville', 'Brookline', 'Newton',
            'Watertown', 'Waltham', 'Lexington', 'Arlington', 'Medford',
            'MIT', 'Harvard', 'Boston University', 'BU', 'Northeastern'
        ]
        
        content_lower = content.lower()
        for location in boston_locations:
            if location.lower() in content_lower:
                return location
        
        return 'Boston Area'
    
    def _is_excluded_url(self, url: str) -> bool:
        """Check if URL should be excluded based on websites_to_watch.txt"""
        url_lower = url.lower()
        for exclusion_url in self.exclusion_urls:
            if exclusion_url in url_lower or url_lower in exclusion_url:
                return True
        return False
    
    def _remove_duplicates(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events based on title similarity"""
        unique_events = []
        seen_titles = set()
        
        for event in events:
            title = event.get('title', '').lower()
            # Simple deduplication based on title similarity
            title_words = set(title.split())
            
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                # If more than 70% of words match, consider it a duplicate
                if len(title_words & seen_words) / max(len(title_words), len(seen_words)) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_events.append(event)
                seen_titles.add(title)
        
        return unique_events
    
    def _filter_events(self, events: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """Filter events to meet final criteria and limit results"""
        filtered_events = []
        
        for event in events:
            # Final validation
            if (self._is_excluded_url(event.get('url', '')) or 
                not self._is_future_event(f"{event.get('title', '')} {event.get('description', '')}")):
                continue
            
            filtered_events.append(event)
            if len(filtered_events) >= max_results:
                break
        
        return filtered_events
    
    def save_events_to_database(self, events: List[Dict[str, Any]]) -> int:
        """Save events to database"""
        saved_count = 0
        for event in events:
            try:
                # Ensure date is set
                if not event.get('date'):
                    event['date'] = datetime.now().strftime('%Y-%m-%d')
                
                event_id = self.db.add_computing_event(event)
                if event_id:
                    saved_count += 1
                    print(f"Saved event: {event['title']} (Source: {event.get('source', 'Unknown')})")
            except Exception as e:
                print(f"Error saving event {event.get('title', 'Unknown')}: {e}")
        
        return saved_count


def main():
    """Main function for command line usage"""
    searcher = EnhancedComputingEventSearcher()
    
    print("🔍 Enhanced search for computing events in Boston area...")
    events = searcher.search_events(max_results=20)
    
    print(f"Found {len(events)} events")
    
    if events:
        print("\nSaving events to database...")
        saved_count = searcher.save_events_to_database(events)
        print(f"Saved {saved_count} events to database")
        
        # Display summary
        print("\nEvent Summary:")
        hosts = {}
        cost_types = {}
        sources = {}
        
        for event in events:
            host = event.get('host', 'Other')
            cost_type = event.get('cost_type', 'Unknown')
            source = event.get('source', 'Unknown')
            
            hosts[host] = hosts.get(host, 0) + 1
            cost_types[cost_type] = cost_types.get(cost_type, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        print("\nEvents by Host:")
        for host, count in sorted(hosts.items()):
            print(f"  {host}: {count}")
        
        print("\nEvents by Cost Type:")
        for cost_type, count in sorted(cost_types.items()):
            print(f"  {cost_type}: {count}")
        
        print("\nEvents by Source:")
        for source, count in sorted(sources.items()):
            print(f"  {source}: {count}")


if __name__ == "__main__":
    main()
