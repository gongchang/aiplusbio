#!/usr/bin/env python3
"""
Improved Tavily-only searcher with better date filtering and relevance.
This focuses on getting better results from Tavily API with improved date range filtering.
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from database import Database


class ImprovedTavilySearcher:
    def __init__(self, db_path='events.db'):
        self.db = Database(db_path)
        self.tavily_api_key = os.getenv('Tavily_API')
        self.tavily_base_url = "https://api.tavily.com/search"
        
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
        """Search for computing events using improved Tavily API with multiple targeted queries"""
        all_events = []
        
        print(f"🔍 Improved search for computing events in Boston area (next 6 months)")
        print(f"📅 Date range: {self.date_range['start_date']} to {self.date_range['end_date']}")
        print(f"🎯 Max results: {max_results}")
        print("-" * 60)
        
        # Multiple targeted searches for better results
        search_queries = [
            self._build_ai_conference_query(),
            self._build_ml_workshop_query(),
            self._build_cloud_computing_query(),
            self._build_bioinformatics_query(),
            self._build_devops_query()
        ]
        
        for i, query in enumerate(search_queries, 1):
            if not query:
                continue
                
            print(f"🔍 Search {i}/5: {query[:100]}...")
            events = self._search_tavily_with_query(query, max_results // len(search_queries))
            all_events.extend(events)
        
        # Remove duplicates and filter
        unique_events = self._remove_duplicates(all_events)
        filtered_events = self._filter_events(unique_events, max_results)
        
        print(f"✅ Found {len(filtered_events)} unique events meeting all criteria")
        return filtered_events
    
    def _build_ai_conference_query(self) -> str:
        """Build query specifically for AI conferences"""
        return 'AI conference Boston 2025 OR "artificial intelligence" conference Cambridge OR AI symposium MIT OR "AI agents" workshop Harvard'
    
    def _build_ml_workshop_query(self) -> str:
        """Build query specifically for machine learning workshops"""
        return '"machine learning" workshop Boston 2025 OR ML training Cambridge OR "deep learning" conference Massachusetts OR ML symposium MIT'
    
    def _build_cloud_computing_query(self) -> str:
        """Build query specifically for cloud computing events"""
        return '"cloud computing" conference Boston 2025 OR "AWS" workshop Cambridge OR "Azure" training Massachusetts OR "Google Cloud" summit'
    
    def _build_bioinformatics_query(self) -> str:
        """Build query specifically for bioinformatics events"""
        return 'bioinformatics conference Boston 2025 OR "computational biology" workshop Cambridge OR genomics symposium MIT OR "precision medicine" conference Harvard'
    
    def _build_devops_query(self) -> str:
        """Build query specifically for DevOps events"""
        return 'DevOps conference Boston 2025 OR "Kubernetes" workshop Cambridge OR "Docker" training Massachusetts OR "CI/CD" summit'
    
    def _search_tavily_with_query(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Tavily API with a specific query"""
        try:
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
                    event = self._extract_event_from_result(result)
                    if event and not self._is_excluded_url(event.get('url', '')):
                        events.append(event)
            
            return events
            
        except Exception as e:
            print(f"Error searching Tavily: {e}")
            return []
    
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
    
    def _extract_event_from_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                'source': 'Tavily'
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
                'eventbrite.com': 'Eventbrite',
                'mit.edu': 'MIT',
                'harvard.edu': 'Harvard',
                'bu.edu': 'Boston University',
                'northeastern.edu': 'Northeastern'
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
                    print(f"Saved event: {event['title']}")
            except Exception as e:
                print(f"Error saving event {event.get('title', 'Unknown')}: {e}")
        
        return saved_count


def main():
    """Main function for command line usage"""
    searcher = ImprovedTavilySearcher()
    
    print("🔍 Improved search for computing events in Boston area...")
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
        
        for event in events:
            host = event.get('host', 'Other')
            cost_type = event.get('cost_type', 'Unknown')
            
            hosts[host] = hosts.get(host, 0) + 1
            cost_types[cost_type] = cost_types.get(cost_type, 0) + 1
        
        print("\nEvents by Host:")
        for host, count in sorted(hosts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {host}: {count}")
        
        print("\nEvents by Cost Type:")
        for cost_type, count in sorted(cost_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cost_type}: {count}")


if __name__ == "__main__":
    main()




