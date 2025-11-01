"""
Enhanced Tech Computing Event Searcher
Focused on tech company events, both virtual and Boston-area local events.
Prioritizes events from major tech companies and developer communities.
"""

import os
import re
import json
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from database import Database
from improved_date_extractor import ImprovedDateExtractor


def _load_env_file(env_path: str = '.env') -> None:
    """Best-effort .env loader (no external deps)."""
    try:
        if not os.path.exists(env_path):
            return
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                if s.startswith('export '):
                    s = s[len('export '):].strip()
                if '=' not in s:
                    continue
                key, val = s.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # normalize smart quotes and whitespace
                for ch in ['“','”','’','‘']:
                    val = val.replace(ch, '')
                if not key or not val or '${' in val:
                    continue
                os.environ.setdefault(key, val)
    except Exception:
        pass


class EnhancedTechComputingSearcher:
    def __init__(self, db_path='events.db'):
        self.db = Database(db_path)
        # Ensure .env is loaded before reading keys
        _load_env_file()
        # Normalize key names
        self.tavily_api_key = os.getenv('TAVILY_API_KEY') or os.getenv('Tavily_API')
        self.eventbrite_api_key = os.getenv('EVENTBRITE_API_KEY')
        # sanitize keys to avoid unicode quotes
        def _sanitize(v: Optional[str]) -> Optional[str]:
            if not v:
                return v
            for ch in ['“','”','’','‘']:
                v = v.replace(ch, '')
            return v.strip()
        self.tavily_api_key = _sanitize(self.tavily_api_key)
        self.eventbrite_api_key = _sanitize(self.eventbrite_api_key)
        self.tavily_base_url = "https://api.tavily.com/search"
        self.eventbrite_base_url = "https://www.eventbriteapi.com/v3"
        
        # Enhanced keywords for tech-focused events
        self.tech_keywords = [
            # AI & Machine Learning
            'AI', 'artificial intelligence', 'machine learning', 'ML', 'deep learning',
            'neural networks', 'computer vision', 'NLP', 'natural language processing',
            'generative AI', 'LLM', 'large language models', 'GPT', 'transformer',
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Jupyter', 'Spark',
            'agent', 'agents', 'AI agent', 'MLops', 'MLOps', 'ML Ops',
            
            # Software Development & Engineering
            'software engineering', 'software development', 'programming', 'coding',
            'full stack', 'frontend', 'backend', 'mobile development', 'web development',
            'API', 'microservices', 'architecture', 'system design', 'algorithms',
            
            # Web Frameworks & Languages
            'React', 'Vue', 'Angular', 'Next.js', 'TypeScript', 'JavaScript', 'Node.js',
            'GraphQL', 'REST API', 'Svelte', 'Tailwind CSS', 'Express.js',
            'Python', 'Java', 'Go', 'Rust', 'Swift', 'Kotlin',
            
            # Backend & Databases
            'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'FastAPI', 'Django', 'Flask', 'Spring Boot',
            
            # Cloud & DevOps
            'cloud computing', 'AWS', 'Azure', 'Google Cloud', 'GCP', 'devops', 'DevOps',
            'kubernetes', 'docker', 'containers', 'infrastructure', 'scalability',
            'serverless', 'edge computing', 'distributed systems',
            'CI/CD', 'GitHub Actions', 'Terraform', 'Ansible', 'Jenkins', 'GitLab',
            'monitoring', 'observability', 'Prometheus', 'Grafana',
            
            # Data & Analytics
            'data science', 'data engineering', 'big data', 'analytics', 'data visualization',
            'business intelligence', 'ETL', 'data pipeline', 'database', 'SQL', 'NoSQL',
            'Snowflake', 'Databricks', 'Airflow', 'dbt',
            
            # Emerging Technologies
            'blockchain', 'cryptocurrency', 'Web3', 'metaverse', 'AR', 'VR',
            'IoT', 'internet of things', 'quantum computing', 'robotics',
            'automation', 'RPA', 'low-code', 'no-code',
            'AI automation', 'ML automation', 'intelligent automation',
            
            # Mobile Development
            'iOS', 'Android', 'Flutter', 'React Native',
            
            # Security & Testing
            'cybersecurity', 'penetration testing', 'security', 'OWASP',
            'testing', 'QA', 'test automation', 'Selenium', 'Cypress', 'TDD',
            
            # Product & Business
            'product management', 'product strategy', 'user experience', 'UX', 'UI',
            'design thinking', 'agile', 'scrum', 'startup', 'entrepreneurship',
            'innovation', 'digital transformation', 'technology trends'
        ]
        
        # Tech company event keywords
        self.tech_company_keywords = [
            'Google', 'Microsoft', 'Amazon', 'Meta', 'Facebook', 'Apple', 'NVIDIA',
            'Intel', 'IBM', 'Oracle', 'Salesforce', 'Adobe', 'Netflix', 'Uber',
            'Airbnb', 'LinkedIn', 'Twitter', 'X', 'GitHub', 'Docker', 'Red Hat',
            'VMware', 'Cisco', 'Atlassian', 'Slack', 'Zoom', 'Dropbox', 'Box',
            'Okta', 'Palo Alto', 'CrowdStrike', 'Splunk', 'Databricks', 'Snowflake',
            'MongoDB', 'Redis', 'Elastic', 'Confluent', 'HashiCorp', 'Stripe',
            'Square', 'PayPal', 'Shopify', 'Twilio', 'SendGrid', 'Mailchimp',
            'HubSpot', 'Salesforce', 'Workday', 'ServiceNow', 'Zendesk'
        ]
        
        # Event type keywords (broader scope)
        self.event_keywords = [
            'conference', 'summit', 'workshop', 'tutorial', 'seminar', 'webinar',
            'meetup', 'meeting', 'event', 'session', 'talk', 'presentation',
            'demo', 'demo day', 'hackathon', 'competition', 'contest', 'challenge',
            'training', 'course', 'bootcamp', 'certification', 'exam',
            'launch', 'announcement', 'keynote', 'panel', 'roundtable',
            'community day', 'developer day', 'tech day', 'innovation day',
            'user group', 'user conference', 'customer conference',
            # Casual/Informal event types
            'coding night', 'dev night', 'tech talk', 'tech talk series',
            'code review', 'pair programming', 'mob programming', 'TDD',
            'code kata', 'lightning talk', 'tech lunch', 'brown bag',
            'office hours', 'Q&A', 'fireside chat', 'unconference',
            'bar camp', 'code retreat', 'study group', 'reading group'
        ]
        
        # Boston area keywords (expanded)
        self.boston_keywords = [
            'Boston', 'Cambridge', 'Somerville', 'Brookline', 'Newton',
            'Watertown', 'Waltham', 'Lexington', 'Arlington', 'Medford',
            'Massachusetts', 'MA', 'Greater Boston', 'Boston area',
            'MIT', 'Harvard', 'Boston University', 'BU', 'Northeastern',
            'Tufts', 'Brandeis', 'Bentley', 'Babson', 'Suffolk',
            # Neighborhoods
            'Back Bay', 'Financial District', 'Seaport', 'Kendall Square',
            'Central Square', 'Davis Square', 'Porter Square',
            'South Boston', 'Southie', 'Dorchester', 'Roxbury', 'Allston',
            'Brighton', 'Jamaica Plain', 'JP', 'Charlestown', 'East Boston',
            'North End', 'West End', 'Beacon Hill', 'Fenway',
            'Longwood', 'Kenmore', 'Mass Ave', 'Comm Ave'
        ]
        
        # Virtual event keywords
        self.virtual_keywords = [
            'virtual', 'online', 'remote', 'digital', 'webinar', 'live stream',
            'livestream', 'zoom', 'teams', 'webex', 'gotomeeting', 'youtube',
            'twitch', 'facebook live', 'linkedin live', 'global', 'worldwide'
        ]
        
        # Load exclusion URLs
        self.exclusion_urls = self._load_exclusion_urls()
        
        # Load corporate event URLs
        self.corporate_event_urls = self._load_corporate_event_urls()
        
        # Date range for search (next 6 months)
        self.date_range = self._get_date_range()
        
        # Initialize improved date extractor
        self.date_extractor = ImprovedDateExtractor()
        
        # RSS feeds for tech companies and communities - ONLY actual event feeds
        # Note: Google/Microsoft feeds tested - they return 0 entries (likely don't exist or are empty)
        # Keeping Meetup RSS feeds which are working
        self.tech_rss_feeds = [
            # Major Tech Company Event Feeds (commented out - these feeds return 0 entries)
            # 'https://developers.google.com/events/feed',  # Returns 0 entries
            # 'https://cloud.google.com/events/feed',  # Returns 0 entries
            # 'https://techcommunity.microsoft.com/events/feed',  # Returns 0 entries
            
            # Boston Tech Meetup Groups (RSS feeds with event-level URLs)
            # Using verified working Meetup group URLs
            'https://www.meetup.com/bostonpython/events/rss/',
            'https://www.meetup.com/Boston-Machine-Learning/events/rss/',
            'https://www.meetup.com/Boston-Data-Science/events/rss/',
            'https://www.meetup.com/Boston-AI/events/rss/',
            'https://www.meetup.com/Boston-Cloud-Computing/events/rss/',
            'https://www.meetup.com/Boston-DevOps/events/rss/',
            'https://www.meetup.com/Boston-Startups/events/rss/',
            'https://www.meetup.com/Boston-Product-Management/events/rss/',
            'https://www.meetup.com/Boston-Entrepreneurs/events/rss/',
            'https://www.meetup.com/Boston-Code-and-Coffee/events/rss/',
            'https://www.meetup.com/Boston-React/events/rss/',
            'https://www.meetup.com/Cambridge-Tech-Meetup/events/rss/',
            'https://www.meetup.com/boston-software-craftsmanship/events/rss/',
            'https://www.meetup.com/boston-js/events/rss/',
            'https://www.meetup.com/Boston-New-Technology/events/rss/'
        ]
    
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
    
    def _load_corporate_event_urls(self) -> List[str]:
        """Load URLs from Corporate_events.txt for customized scraping"""
        corporate_urls = []
        try:
            with open('Corporate_events.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Allow lines that contain 'http' anywhere (not just start with)
                    if line and not line.startswith('#'):
                        # Extract URL if http is in the line
                        if 'http' in line.lower():
                            # Clean up the URL - take everything that looks like a URL
                            import re
                            url_match = re.search(r'https?://[^\s]+', line)
                            if url_match:
                                url = url_match.group(0).rstrip('/').rstrip(')').rstrip(']')
                                if url not in corporate_urls:
                                    corporate_urls.append(url)
        except FileNotFoundError:
            print("Warning: Corporate_events.txt not found")
        return corporate_urls
    
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
    
    def search_events(self, max_results: int = 30) -> List[Dict[str, Any]]:
        """Search for tech-focused computing events"""
        all_events = []
        
        print(f"🔍 Enhanced tech search for computing events (Boston + Virtual)")
        print(f"📅 Date range: {self.date_range['start_date']} to {self.date_range['end_date']}")
        print(f"🎯 Max results: {max_results}")
        print("-" * 60)
        
        # 1. Search tech company RSS feeds
        rss_events = self._search_tech_rss_feeds(max_results // 4)
        all_events.extend(rss_events)
        
        # 2. Search Eventbrite for tech events
        if self.eventbrite_api_key:
            eventbrite_events = self._search_tech_eventbrite_events(max_results // 4)
            all_events.extend(eventbrite_events)
        else:
            print("⚠️  Eventbrite API key not found - skipping Eventbrite search")
        
        # 3. Search Tavily with tech-focused queries
        if self.tavily_api_key:
            tavily_events = self._search_tech_tavily_events(max_results // 2)
            all_events.extend(tavily_events)
        else:
            print("⚠️  Tavily API key not found - skipping Tavily search")
        
        # 4. Search Boston tech meetup groups
        meetup_events = self._search_boston_tech_meetups(max_results // 4)
        all_events.extend(meetup_events)
        
        # 5. Search corporate event URLs (customized source)
        if self.corporate_event_urls:
            corporate_events = self._search_corporate_events(max_results // 4)
            all_events.extend(corporate_events)
        else:
            print("⚠️  No corporate event URLs found - skipping customized scraping")
        
        # Remove duplicates and filter
        unique_events = self._remove_duplicates(all_events)
        filtered_events = self._filter_tech_events(unique_events, max_results)
        
        print(f"✅ Found {len(filtered_events)} unique tech events meeting criteria")
        return filtered_events
    
    def _search_tech_rss_feeds(self, max_results: int) -> List[Dict[str, Any]]:
        """Search RSS feeds from tech companies and communities"""
        print("📡 Searching tech company RSS feeds...")
        events = []
        
        for feed_url in self.tech_rss_feeds:
            try:
                print(f"  📡 Checking: {feed_url}")
                
                # For Meetup feeds, use requests with user agent to avoid blocking
                is_meetup = 'meetup.com' in feed_url
                if is_meetup:
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                        }
                        response = requests.get(feed_url, headers=headers, timeout=15)
                        if response.status_code == 200:
                            feed = feedparser.parse(response.text)
                        else:
                            feed = feedparser.parse(feed_url)
                    except:
                        feed = feedparser.parse(feed_url)
                else:
                    feed = feedparser.parse(feed_url)
                
                # For Meetup feeds, process more entries since they have specific event URLs
                if is_meetup:
                    entries_to_process = min(max_results, len(feed.entries))
                else:
                    entries_to_process = max_results // max(len(self.tech_rss_feeds), 1)
                
                for entry in feed.entries[:entries_to_process]:
                    event = self._extract_tech_rss_event(entry, feed_url)
                    if event:
                        # For RSS feeds (especially Meetup), trust them - they're already curated tech events
                        # Skip tech criteria check for all RSS feeds since they're from trusted sources
                        events.append(event)
                        
            except Exception as e:
                print(f"  ❌ Error with RSS feed {feed_url}: {e}")
                continue
        
        print(f"Tech RSS feeds found {len(events)} relevant events")
        return events
    
    def _extract_tech_rss_event(self, entry, feed_url: str) -> Optional[Dict[str, Any]]:
        """Extract event information from tech RSS entry"""
        try:
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # For Meetup RSS feeds, always extract (they have individual event URLs)
            is_meetup = 'meetup.com' in feed_url
            
            # Check if event contains tech keywords (skip for Meetup as they're already tech-focused)
            if not is_meetup and not any(keyword.lower() in title.lower() for keyword in self.tech_keywords):
                return None
            
            # Extract event URL - use entry link which should be the specific event page
            event_url = entry.get('link', '')
            
            # Extract event details
            event = {
                'title': title,
                'description': entry.get('description', ''),
                'url': event_url,  # This should be the individual event page URL
                'source_url': feed_url,
                'is_virtual': self._is_virtual_event(entry.get('description', '')),
                'requires_registration': 'register' in entry.get('description', '').lower() or is_meetup,
                'categories': self._extract_tech_categories(title),
                'host': self._extract_tech_host(feed_url),
                'cost_type': self._determine_cost_type(entry.get('description', '')),
                'date': self._extract_event_date_from_rss(entry),
                'time': self._extract_event_time_from_rss(entry),
                'location': self._extract_tech_location(entry),
                'source': 'Meetup RSS' if is_meetup else 'Tech RSS Feed'
            }
            
            # Only return if we have a valid future date and URL
            if event.get('date') and event.get('url'):
                return event
            
            return None
            
        except Exception as e:
            print(f"Error extracting tech RSS event: {e}")
            return None
    
    def _extract_tech_host(self, feed_url: str) -> str:
        """Extract tech company host from RSS feed URL"""
        host_mapping = {
            'google.com': 'Google',
            'microsoft.com': 'Microsoft',
            'aws.amazon.com': 'Amazon Web Services',
            'nvidia.com': 'NVIDIA',
            'docker.com': 'Docker',
            'kubernetes.io': 'Kubernetes',
            'cncf.io': 'CNCF',
            'huggingface.co': 'Hugging Face',
            'redhat.com': 'Red Hat',
            'github.com': 'GitHub',
            'dev.to': 'DEV Community',
            'stackoverflow.com': 'Stack Overflow',
            'infoq.com': 'InfoQ',
            'thenewstack.io': 'The New Stack',
            'oreilly.com': 'O\'Reilly',
            'techcrunch.com': 'TechCrunch',
            'venturebeat.com': 'VentureBeat',
            'wired.com': 'Wired',
            'meetup.com': 'Meetup'
        }
        
        for domain, host_name in host_mapping.items():
            if domain in feed_url:
                return host_name
        
        return 'Tech Community'
    
    def _extract_tech_categories(self, title: str) -> List[str]:
        """Extract tech categories from title"""
        categories = []
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
            categories.append('AI/ML')
        if any(keyword in title_lower for keyword in ['cloud', 'aws', 'azure', 'gcp', 'devops']):
            categories.append('Cloud/DevOps')
        if any(keyword in title_lower for keyword in ['data', 'analytics', 'data science']):
            categories.append('Data Science')
        if any(keyword in title_lower for keyword in ['software', 'development', 'programming', 'coding']):
            categories.append('Software Development')
        if any(keyword in title_lower for keyword in ['product', 'ux', 'ui', 'design']):
            categories.append('Product/Design')
        if any(keyword in title_lower for keyword in ['startup', 'entrepreneurship', 'business']):
            categories.append('Startup/Business')
        
        return categories if categories else ['Technology']
    
    def _extract_tech_location(self, entry) -> str:
        """Extract location from tech RSS entry"""
        description = entry.get('description', '').lower()
        
        # Check for virtual events first
        if any(keyword in description for keyword in self.virtual_keywords):
            return 'Virtual'
        
        # Look for Boston area locations
        for location in self.boston_keywords:
            if location.lower() in description:
                return location
        
        return 'Virtual'  # Default to virtual for tech events
    
    def _search_tech_eventbrite_events(self, max_results: int) -> List[Dict[str, Any]]:
        """Search for FREE tech workshops/webinars/trainings using Eventbrite API"""
        print("🎫 Searching Eventbrite for free tech workshops/webinars/trainings...")
        
        if not self.eventbrite_api_key:
            print("  ⚠️  Eventbrite API key not available")
            return []
        
        all_events = []
        
        # Search multiple locations: Boston, and we'll filter for virtual events separately
        search_locations = [
            {'location': 'Boston, MA', 'within': '50mi', 'is_virtual': False}
        ]
        
        try:
            headers = {
                'Authorization': f'Bearer {self.eventbrite_api_key}'
            }
            
            # Eventbrite API v3: /events/ requires organizer_id or venue_id
            # Alternative: Use organizers endpoint to find tech organizers, then get their events
            # OR: Use discovery page scraping (fallback if API doesn't support public search)
            
            # Try approach 1: Find organizers by location, then get their events
            try:
                # Search for organizers in Boston area with tech-related keywords
                organizer_params = {
                    'location.address': 'Boston, MA',
                    'location.within': '50mi'
                }
                
                # Try to get my own organizer events first (if API key is for a user account)
                user_response = requests.get(
                    f'{self.eventbrite_base_url}/users/me/',
                    headers=headers,
                    timeout=15
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    organizer_id = user_data.get('id')
                    if organizer_id:
                        # Get events for this organizer
                        events_response = requests.get(
                            f'{self.eventbrite_base_url}/organizers/{organizer_id}/events/',
                            headers=headers,
                            params={'expand': 'ticket_classes,venue', 'status': 'live'},
                            timeout=15
                        )
                        if events_response.status_code == 200:
                            events_data = events_response.json()
                            events_found = events_data.get('events', [])
                            
                            for event_data in events_found[:20]:
                                # Check if free and workshop type
                                is_free = event_data.get('is_free', False)
                                name = event_data.get('name', {}).get('text', '').lower()
                                desc = event_data.get('description', {}).get('text', '').lower()
                                
                                is_workshop = any(kw in f"{name} {desc}" for kw in [
                                    'workshop', 'webinar', 'training', 'bootcamp', 'tutorial',
                                    'meetup', 'hackathon', 'hands-on', 'developer', 'coding'
                                ])
                                
                                if is_free and is_workshop:
                                    event = self._extract_tech_eventbrite_event(event_data)
                                    if event and self._is_free_workshop_event(event):
                                        all_events.append(event)
            except Exception as e:
                print(f"  ⚠️  Eventbrite organizer approach failed: {e}")
            
            # Approach 2: Try scraping Eventbrite discovery pages for Boston tech events
            try:
                discovery_urls = [
                    'https://www.eventbrite.com/d/ma--boston/technology--events/',
                    'https://www.eventbrite.com/d/online/technology--events/'
                ]
                
                for discovery_url in discovery_urls:
                    try:
                        scrape_events = self._scrape_eventbrite_discovery_page(discovery_url)
                        all_events.extend(scrape_events)
                    except Exception as e:
                        print(f"  ⚠️  Error scraping {discovery_url}: {e}")
                        continue
            except Exception as e:
                print(f"  ⚠️  Eventbrite discovery scraping error: {e}")
            
            print(f"Eventbrite found {len(all_events)} free tech workshops/webinars/trainings")
            return all_events
            
        except Exception as e:
            print(f"Error searching Eventbrite: {e}")
            return []
    
    def _scrape_eventbrite_discovery_page(self, discovery_url: str) -> List[Dict[str, Any]]:
        """Scrape Eventbrite discovery page to extract individual event URLs"""
        events = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }
            response = requests.get(discovery_url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                return events
            
            html = response.text
            
            # Find Eventbrite event links - multiple patterns
            import re
            
            # Pattern 1: Full URLs https://www.eventbrite.com/e/[name]-tickets-[id]...
            full_urls = re.findall(r'href="(https://www\.eventbrite\.com/e/[^"]+-tickets-([0-9]+))', html)
            
            # Pattern 2: data-event-id attributes
            data_ids = re.findall(r'data-event-id="([0-9]+)"', html)
            
            # Combine both sources
            event_ids = set()
            for url, event_id in full_urls[:15]:  # Limit from URLs
                event_ids.add(event_id)
            for event_id in data_ids[:15]:  # Limit from data attributes
                event_ids.add(event_id)
            
            seen_ids = set()
            for event_id in list(event_ids)[:15]:  # Limit to 15 events per page
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                
                # Try to get event details via API using the event ID
                try:
                    headers_api = {'Authorization': f'Bearer {self.eventbrite_api_key}'}
                    event_response = requests.get(
                        f'{self.eventbrite_base_url}/events/{event_id}/',
                        headers=headers_api,
                        params={'expand': 'ticket_classes,venue,organizer'},
                        timeout=15
                    )
                    
                    if event_response.status_code == 200:
                        event_data = event_response.json()
                        
                        # Check if free and workshop type
                        is_free = event_data.get('is_free', False)
                        name = event_data.get('name', {}).get('text', '')
                        desc = event_data.get('description', {}).get('text', '').lower()
                        name_lower = name.lower()
                        
                        is_workshop = any(kw in f"{name_lower} {desc}" for kw in [
                            'workshop', 'webinar', 'training', 'bootcamp', 'tutorial',
                            'meetup', 'hackathon', 'hands-on', 'developer', 'coding'
                        ])
                        
                        # Check if Boston or virtual
                        is_virtual = event_data.get('is_online_event', False)
                        venue = event_data.get('venue', {})
                        venue_address = venue.get('address', {}) if venue else {}
                        city = venue_address.get('city', '').lower()
                        is_boston = 'boston' in city or 'cambridge' in city or 'boston' in name_lower
                        
                        # Relaxed filtering: Allow free events OR workshop-type events in Boston/virtual
                        # This increases the number of relevant events while maintaining quality
                        if not (is_virtual or is_boston):
                            continue  # Must be in Boston/virtual
                        
                        # Accept if: (free) OR (workshop-type) OR (free workshop)
                        if is_free or is_workshop:
                            # If paid, must be workshop-type
                            if not is_free and not is_workshop:
                                continue
                            
                            # If we get here, event meets relaxed criteria
                            event = self._extract_tech_eventbrite_event(event_data)
                            if event:
                                events.append(event)
                except Exception as e:
                    # Skip if API call fails
                    continue
                    
        except Exception as e:
            print(f"  ⚠️  Error scraping Eventbrite discovery page: {e}")
        
        return events
    
    def _is_free_workshop_event(self, event: Dict[str, Any]) -> bool:
        """Check if event is a free workshop/webinar/training"""
        title = event.get('title', '').lower()
        desc = event.get('description', '').lower()
        combined = f"{title} {desc}"
        
        # Must be free
        if event.get('cost_type', '').lower() not in ['free', 'free (likely)']:
            return False
        
        # Must be workshop, webinar, training, meetup, or hackathon
        preferred_types = ['workshop', 'webinar', 'training', 'bootcamp', 'tutorial', 
                         'meetup', 'hackathon', 'hands-on', 'one-day', 'one day']
        if not any(pt in combined for pt in preferred_types):
            return False
        
        # Must be Boston local or virtual
        location = event.get('location', '').lower()
        is_virtual = event.get('is_virtual', False)
        is_boston = any(b in location or b in combined for b in self.boston_keywords)
        
        return is_virtual or is_boston
    
    def _extract_tech_eventbrite_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract tech event information from Eventbrite API response"""
        try:
            name = event_data.get('name', {}).get('text', '').strip()
            if not name:
                return None
            
            name_lower = name.lower()
            description = event_data.get('description', {}).get('text', '').lower()
            combined = f"{name_lower} {description}"
            
            # For Eventbrite, we're already searching for tech-related terms, so be more lenient
            # Just check if it's a workshop/webinar/training OR has tech keywords
            is_workshop_type = any(term in combined for term in [
                'workshop', 'webinar', 'training', 'bootcamp', 'tutorial', 'meetup',
                'hackathon', 'hands-on', 'developer', 'coding', 'programming'
            ])
            has_tech_keywords = any(keyword.lower() in combined for keyword in self.tech_keywords)
            
            # Accept if it's a workshop type OR has tech keywords
            if not (is_workshop_type or has_tech_keywords):
                return None
            
            # Extract event details
            event = {
                'title': name,
                'description': event_data.get('description', {}).get('text', ''),
                'url': event_data.get('url', ''),
                'source_url': event_data.get('url', ''),
                'is_virtual': event_data.get('is_online_event', False),
                'requires_registration': True,
                'categories': self._extract_tech_categories(name),
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
                organizer_name = organizer.get('name', 'Other')
                # Check if it's a known tech company
                for tech_company in self.tech_company_keywords:
                    if tech_company.lower() in organizer_name.lower():
                        return tech_company
                return organizer_name
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
            if event_data.get('is_online_event'):
                return 'Virtual'
            
            venue = event_data.get('venue', {})
            if venue:
                address = venue.get('address', {})
                city = address.get('city', '')
                state = address.get('region', '')
                if city and state:
                    return f"{city}, {state}"
                elif city:
                    return city
            
            return 'Boston Area'
        except:
            return 'Boston Area'
    
    def _search_tech_tavily_events(self, max_results: int) -> List[Dict[str, Any]]:
        """Search for tech events using Tavily API with enhanced queries"""
        print("🔍 Searching Tavily API for tech events...")
        
        # Focused queries for hands-on workshops, webinars, trainings, one-day events
        # Prioritize ML/AI/LLM/DevOps/MLops/agent events (user's focus areas)
        # Prioritize Boston local and virtual events
        # Note: Not searching for "free" - cost filtering happens post-search
        search_queries = [
            # Developer Workshops & Trainings (Boston) - General
            'Boston developer workshop 2026',
            'Boston coding bootcamp 2026',
            'Boston tech training 2026',
            'Boston developer meetup 2026',
            'Cambridge tech workshop 2026',
            
            # ML/AI/LLM Workshops (Boston) - Priority Focus
            'Boston AI workshop 2026',
            'Boston machine learning workshop 2026',
            'Boston ML workshop 2026',
            'Boston LLM workshop 2026',
            'Boston large language models workshop 2026',
            'Boston AI agent workshop 2026',
            'Boston MLops workshop 2026',
            'Boston ML Ops training 2026',
            'Boston AI automation workshop 2026',
            
            # DevOps Workshops (Boston) - Priority Focus
            'Boston DevOps workshop 2026',
            'Boston DevOps training 2026',
            'Boston CI/CD workshop 2026',
            'Boston infrastructure workshop 2026',
            
            # Other Tech Workshops (Boston)
            'Boston data science workshop 2026',
            'Boston web development workshop 2026',
            'Boston cloud computing workshop 2026',
            
            # Workshops by Technology/Framework (Boston)
            'React workshop Boston 2026',
            'Python workshop Boston 2026',
            'JavaScript meetup Boston 2026',
            'Node.js workshop Boston 2026',
            'TypeScript workshop Boston 2026',
            'Docker workshop Boston 2026',
            'Kubernetes workshop Boston 2026',
            'Git workshop Boston 2026',
            'cybersecurity workshop Boston 2026',
            
            # Virtual Workshops & Webinars - General
            'virtual developer workshop 2026',
            'online coding workshop 2026',
            'virtual tech training 2026',
            
            # Virtual ML/AI/LLM Workshops - Priority Focus
            'virtual AI webinar 2026',
            'virtual machine learning workshop 2026',
            'virtual ML workshop 2026',
            'virtual LLM workshop 2026',
            'virtual AI agent training 2026',
            'virtual MLops workshop 2026',
            'virtual DevOps training 2026',
            
            # Virtual Other Tech Workshops
            'virtual data science workshop 2026',
            'virtual web development workshop 2026',
            'virtual cloud workshop 2026',
            
            # Virtual Workshops by Technology/Framework
            'virtual React workshop 2026',
            'virtual Python training 2026',
            'online JavaScript course 2026',
            'virtual AWS training 2026',
            'online Kubernetes workshop 2026',
            
            # One-Day Events
            'one day tech conference Boston 2026',
            'one day developer conference 2026',
            'tech day Boston 2026',
            'developer day virtual 2026',
            
            # Hackathons & Hands-On Events
            'Boston hackathon 2026',
            'virtual hackathon 2026',
            'Boston coding challenge 2026',
            'coding night Boston 2026',
            'dev night Boston 2026',
            
            # Tech Company Events
            'AWS workshop Boston 2026',
            'Google Cloud workshop virtual 2026',
            'Microsoft Azure workshop 2026',
            'Docker workshop Boston 2026',
            'Kubernetes workshop virtual 2026',
            'GitHub workshop Boston 2026',
            'Microsoft workshop virtual 2026',
            'Google developer event virtual 2026'
        ]
        
        all_events = []
        for i, query in enumerate(search_queries, 1):
            print(f"  🔍 Tavily search {i}/{len(search_queries)}: {query[:60]}...")
            events = self._search_tavily_with_query(query, max_results // len(search_queries))
            all_events.extend(events)
        
        print(f"Tavily found {len(all_events)} relevant tech events")
        return all_events
    
    def _search_tavily_with_query(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Tavily API with a specific query"""
        try:
            # Tavily API format (api_key in payload works)
            # max_results must be at least 1, use 3-5 per query for good coverage
            tavily_max = max(3, min(max_results, 5)) if max_results > 0 else 3
            
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",  # Use basic for faster results
                "max_results": tavily_max
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.tavily_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = response.text[:200] if hasattr(response, 'text') else 'Unknown error'
                print(f"    Tavily API error: {response.status_code} - {error_msg}")
                return []
            
            search_results = response.json()
            events = []
            
            for result in search_results.get('results', []):
                if self._meets_tech_criteria(result):
                    event = self._extract_tech_event_from_result(result)
                    if event and not self._is_excluded_url(event.get('url', '')):
                        events.append(event)
            
            return events
            
        except Exception as e:
            print(f"    Error searching Tavily: {e}")
            return []
    
    def _search_boston_tech_meetups(self, max_results: int) -> List[Dict[str, Any]]:
        """Search Boston tech meetup groups via HTML scraping (fallback if RSS doesn't work)"""
        print("🏙️ Searching Boston tech meetup groups...")
        events = []
        
        # Boston tech meetup group URLs
        meetup_urls = [
            'https://www.meetup.com/Boston-New-Technology/events/',
            'https://www.meetup.com/Boston-Software-Developers/events/',
            'https://www.meetup.com/Boston-Machine-Learning/events/',
            'https://www.meetup.com/Boston-Data-Science/events/',
            'https://www.meetup.com/Boston-AI/events/',
            'https://www.meetup.com/Boston-Cloud-Computing/events/',
            'https://www.meetup.com/Boston-DevOps/events/',
            'https://www.meetup.com/Boston-Startups/events/',
            'https://www.meetup.com/Boston-Product-Management/events/',
            'https://www.meetup.com/Boston-Entrepreneurs/events/'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
        import re
        for url in meetup_urls:
            try:
                print(f"  🏙️ Checking: {url}")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    continue
                
                html = response.text
                
                # Find Meetup event links - pattern: /[group-name]/events/[event-id]/
                event_pattern = r'href="(/([^/]+)/events/([0-9]+)/[^"]*)"'
                matches = re.findall(event_pattern, html)
                
                for event_url_part, group_name, event_id in matches[:5]:  # Limit per group
                    event_url = f"https://www.meetup.com{event_url_part}"
                    
                    # Extract event title and date from HTML if possible
                    # Try to find event details in the HTML around the link
                    title_match = re.search(r'<a[^>]*href="[^"]*{}[^"]*"[^>]*>([^<]+)</a>'.format(re.escape(event_url_part)), html, re.IGNORECASE)
                    title = title_match.group(1).strip() if title_match else f"{group_name.replace('-', ' ')} Event"
                    
                    # Try to extract date from nearby HTML
                    date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', html[html.find(event_url_part)-500:html.find(event_url_part)+500])
                    date_str = ''
                    if date_match:
                        date_str = self.date_extractor.extract_event_date(date_match.group(1), '')
                    
                    if not date_str:
                        # If no date found, skip (we need future dates)
                        continue
                    
                    if not self.date_extractor.is_future_event(date_str):
                        continue
                    
                    event = {
                        'title': title,
                        'description': f'Tech meetup event from {group_name.replace("-", " ")}',
                        'url': event_url,
                        'source_url': url,
                        'is_virtual': 'virtual' in html.lower() or 'online' in html.lower(),
                        'requires_registration': True,
                        'categories': self._extract_tech_categories(title),
                        'host': group_name.replace('-', ' '),
                        'cost_type': 'Free',  # Meetups are typically free
                        'date': date_str,
                        'time': self.date_extractor.extract_event_time(title, '') or '18:00',
                        'location': 'Boston',
                        'source': 'Meetup HTML'
                    }
                    events.append(event)
                    
            except Exception as e:
                print(f"  ❌ Error with meetup {url}: {e}")
                continue
        
        print(f"Boston meetups found {len(events)} relevant events")
        return events
    
    def _search_corporate_events(self, max_results: int) -> List[Dict[str, Any]]:
        """Search for events from corporate event URLs (customized source)"""
        print("🏢 Searching corporate event URLs (Customized source)...")
        events = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
        for url in self.corporate_event_urls:
            try:
                print(f"  🏢 Scraping starting point: {url}")
                response = requests.get(url, headers=headers, timeout=20)
                
                if response.status_code != 200:
                    print(f"    ⚠️  HTTP {response.status_code} for {url}")
                    continue
                
                html = response.text
                
                # Step 1: Extract events directly from the starting page
                page_events = self._extract_events_from_html(html, url)
                
                # Step 2: Find and follow links to individual event pages
                event_links = self._find_event_links(html, url)
                print(f"    📎 Found {len(event_links)} potential event links to follow")
                
                # Also check for pagination or "more events" links
                pagination_links = self._find_pagination_links(html, url)
                if pagination_links:
                    print(f"    📄 Found {len(pagination_links)} pagination links")
                    # Follow first few pagination links to get more events
                    for pag_link in pagination_links[:3]:  # Limit pagination
                        try:
                            pag_response = requests.get(pag_link, headers=headers, timeout=15)
                            if pag_response.status_code == 200:
                                pag_html = pag_response.text
                                pag_events = self._extract_events_from_html(pag_html, pag_link)
                                page_events.extend(pag_events)
                                # Find more event links from paginated pages
                                pag_event_links = self._find_event_links(pag_html, pag_link)
                                event_links.extend(pag_event_links)
                        except:
                            continue
                
                # Follow each event link (limit increased to get more events)
                event_links = list(set(event_links))  # Deduplicate
                print(f"    🔗 Following {min(len(event_links), 50)} event links...")
                for i, event_link in enumerate(event_links[:50], 1):  # Increased limit to 50 links per starting URL
                    try:
                        if i % 10 == 0:
                            print(f"      Processing link {i}/{min(len(event_links), 50)}...")
                        event_detail = self._scrape_event_detail_page(event_link, url, headers)
                        if event_detail:
                            # Only include if Boston or Virtual (per user requirement)
                            location = event_detail.get('location', '').lower()
                            is_virtual = event_detail.get('is_virtual', False)
                            title = event_detail.get('title', '').lower()
                            desc = event_detail.get('description', '').lower()
                            combined = f"{title} {desc} {location}"
                            
                            # Case-insensitive Boston check
                            is_boston = any(b.lower() in combined for b in self.boston_keywords)
                            is_virt = is_virtual or any(v in combined for v in self.virtual_keywords)
                            
                            if is_boston or is_virt:
                                page_events.append(event_detail)
                                # Also check if this event page has links to other events (follow deeper)
                                try:
                                    response = requests.get(event_link, headers=headers, timeout=10)
                                    if response.status_code == 200:
                                        nested_links = self._find_event_links(response.text, event_link)
                                        # Add nested links to be processed (up to 5 per event page)
                                        for nested_link in nested_links[:5]:
                                            if nested_link not in event_links:
                                                event_links.append(nested_link)
                                except:
                                    pass
                    except Exception as e:
                        # Silently continue if a link fails
                        continue
                
                # Filter out blog posts/lists
                filtered_page_events = []
                for event in page_events:
                    # Skip if already seen (by URL)
                    if any(e.get('url') == event.get('url') for e in filtered_page_events):
                        continue
                    if not self._is_blog_post_list(event):
                        filtered_page_events.append(event)
                
                events.extend(filtered_page_events)
                print(f"    ✅ Found {len(filtered_page_events)} unique events from {url}")
                
            except Exception as e:
                print(f"    ❌ Error scraping {url}: {e}")
                continue
        
        print(f"🏢 Corporate events found {len(events)} relevant events")
        return events
    
    def _extract_events_from_html(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract event information from HTML content"""
        import re
        events = []
        
        # Common patterns for event extraction
        # Look for common event HTML structures:
        # 1. Event cards/containers with title, date, location
        # 2. Links to event pages
        # 3. Calendar/event list formats
        
        combined_text = html.lower()
        
        # Filter: Skip if this page itself is a blog post/list
        if self._is_blog_post_list({'title': self._extract_title_from_html(html), 'description': html[:1000]}):
            return []
        
        # Pattern 1: Extract event links (common in event listing pages)
        # Look for links that might be events
        event_link_patterns = [
            r'<a[^>]*href="([^"]*event[^"]*)"[^>]*>([^<]+)</a>',
            r'<a[^>]*href="([^"]*workshop[^"]*)"[^>]*>([^<]+)</a>',
            r'<a[^>]*href="([^"]*webinar[^"]*)"[^>]*>([^<]+)</a>',
            r'<a[^>]*href="([^"]*conference[^"]*)"[^>]*>([^<]+)</a>',
        ]
        
        found_urls = set()
        for pattern in event_link_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                event_url = match.group(1)
                event_title = match.group(2).strip()
                
                # Skip if URL already processed or invalid
                if not event_url or event_url.lower() in found_urls:
                    continue
                
                # Normalize URL (make absolute if relative)
                if event_url.startswith('/'):
                    parsed_source = urlparse(source_url)
                    event_url = f"{parsed_source.scheme}://{parsed_source.netloc}{event_url}"
                elif not event_url.startswith('http'):
                    continue
                
                found_urls.add(event_url.lower())
                
                # Try to extract date from surrounding HTML
                match_pos = match.start()
                context = html[max(0, match_pos-300):min(len(html), match_pos+300)]
                
                # Extract date from context
                date_str = self._extract_date_from_context(context)
                if not date_str:
                    # Try to get date from full page
                    date_str = self.date_extractor.extract_event_date(event_title, html)
                
                # Only include future events with valid dates
                if date_str:
                    # Validate date format and sanity check
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        # Sanity check: date should be between 2020 and 2030
                        if date_obj.year < 2020 or date_obj.year > 2030:
                            continue  # Skip invalid dates
                    except ValueError:
                        continue  # Skip invalid date formats
                    
                    if self.date_extractor.is_future_event(date_str, date_str):
                        # Extract location and check if Boston or Virtual
                        location = self._extract_tech_location_from_content(context)
                        location_lower = location.lower()
                        is_virtual = self._is_virtual_event(context)
                        combined_location = f"{event_title} {context} {location}".lower()
                        
                        # Case-insensitive Boston check
                        is_boston = any(b.lower() in combined_location for b in self.boston_keywords)
                        is_virt = is_virtual or any(v in combined_location for v in self.virtual_keywords)
                        
                        # Only include if Boston local OR virtual (user requirement)
                        if is_boston or is_virt:
                            event = {
                                'title': event_title,
                                'description': self._extract_description_from_html(context),
                                'url': event_url,
                                'source_url': source_url,
                                'is_virtual': is_virtual,
                                'requires_registration': 'register' in context.lower() or 'rsvp' in context.lower(),
                                'categories': self._extract_tech_categories(event_title),
                                'host': self._extract_host_from_url(source_url),
                                'cost_type': self._determine_cost_type(context),
                                'date': date_str,
                                'time': self.date_extractor.extract_event_time(event_title, context),
                                'location': location,
                                'source': 'Customized'
                            }
                            events.append(event)
        
        # Pattern 2: Extract from structured data/JSON-LD if present
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        json_ld_matches = re.finditer(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)
        for match in json_ld_matches:
            try:
                json_data = json.loads(match.group(1))
                if isinstance(json_data, dict) and json_data.get('@type') in ['Event', 'TechEvent']:
                    event = self._extract_event_from_json_ld(json_data, source_url)
                    if event:
                        events.append(event)
            except:
                pass
        
        return events
    
    def _find_event_links(self, html: str, source_url: str) -> List[str]:
        """Find links to individual event pages from a listing page"""
        import re
        event_links = []
        found_urls = set()
        
        # Patterns for finding event links - more comprehensive
        link_patterns = [
            # Direct event URLs (most specific)
            r'<a[^>]*href="([^"]*(?:event|workshop|webinar|conference|meetup|training|seminar)[^"]*(?:details|schedule|info|page)[^"]*)"[^>]*',
            r'<a[^>]*href="([^"]*(?:/events/[^"]*details[^"]*|/events/details/[^"]*))"[^>]*',
            r'<a[^>]*href="([^"]*/events/[^"]*)"[^>]*',  # Any /events/ URL
            # Links with event-related classes/IDs
            r'<a[^>]*(?:class|id)="[^"]*event[^"]*"[^>]*href="([^"]+)"',
            r'<a[^>]*(?:class|id)="[^"]*workshop[^"]*"[^>]*href="([^"]+)"',
            r'<a[^>]*(?:class|id)="[^"]*webinar[^"]*"[^>]*href="([^"]+)"',
            # Links in event containers
            r'<div[^>]*(?:class|id)="[^"]*event[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"',
            r'<article[^>]*>.*?<a[^>]*href="([^"]+)"',  # Article tags often contain events
            # Links with data attributes indicating events
            r'<a[^>]*data-[^=]*="[^"]*event[^"]*"[^>]*href="([^"]+)"',
            # Calendar/date links that might be events
            r'<a[^>]*href="([^"]*/\d{4}/\d{2}/[^"]*)"',
            # Event card/tile patterns
            r'<div[^>]*(?:class|id)="[^"]*(?:card|tile|item)[^"]*"[^>]*>.*?<a[^>]*href="([^"]+/events/[^"]+)"',
        ]
        
        for pattern in link_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                href = match.group(1)
                if not href or href.lower() in found_urls:
                    continue
                
                # Normalize URL
                if href.startswith('/'):
                    parsed_source = urlparse(source_url)
                    href = f"{parsed_source.scheme}://{parsed_source.netloc}{href}"
                elif href.startswith('#'):
                    continue
                elif not href.startswith('http'):
                    continue
                
                # Filter: skip obviously non-event URLs
                skip_patterns = [
                    '/blog/', '/news/', '/article/', '/tag/', '/category/',
                    '/search', '/login', '/register', '/about', '/contact',
                    '/account', '/accounts/', '/signup', '/sign-in', '/signin',
                    '/profile', '/settings', '/admin', '/dashboard',
                    '.pdf', '.jpg', '.png', '.gif', '.css', '.js',
                    'mailto:', 'tel:', 'javascript:', '#',
                    '/terms', '/privacy', '/cookie'
                ]
                if any(skip in href.lower() for skip in skip_patterns):
                    continue
                
                # Skip if URL looks like account/login/profile page
                href_lower = href.lower()
                if any(pattern in href_lower for pattern in ['/login', '/logout', '/account', '/profile', '/settings']):
                    continue
                
                # Must be from same domain or related domain
                try:
                    link_domain = urlparse(href).netloc.lower()
                    source_domain = urlparse(source_url).netloc.lower()
                    # Allow same domain or subdomains
                    if link_domain == source_domain or link_domain.endswith('.' + source_domain):
                        found_urls.add(href.lower())
                        event_links.append(href)
                except:
                    continue
        
        return list(set(event_links))  # Remove duplicates
    
    def _find_pagination_links(self, html: str, source_url: str) -> List[str]:
        """Find pagination or 'more events' links"""
        import re
        pagination_links = []
        
        # Common pagination patterns
        patterns = [
            r'<a[^>]*href="([^"]*(?:next|more|page|view-all|see-all)[^"]*)"[^>]*',
            r'<a[^>]*href="([^"]*page[^=]*=\d+[^"]*)"[^>]*',
            r'<a[^>]*href="([^"]*/events/[^"]*)"[^>]*>.*?(?:all|more|next|view)[^<]*</a>',
            r'href="([^"]*/events/\?[^"]*)"',  # Events listing with query params
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                href = match.group(1)
                if not href or href.lower() in [p.lower() for p in pagination_links]:
                    continue
                
                # Normalize URL
                if href.startswith('/'):
                    parsed_source = urlparse(source_url)
                    href = f"{parsed_source.scheme}://{parsed_source.netloc}{href}"
                elif not href.startswith('http'):
                    continue
                
                # Must be same domain
                try:
                    link_domain = urlparse(href).netloc.lower()
                    source_domain = urlparse(source_url).netloc.lower()
                    if link_domain == source_domain or link_domain.endswith('.' + source_domain):
                        pagination_links.append(href)
                except:
                    continue
        
        return list(set(pagination_links))
    
    def _scrape_event_detail_page(self, event_url: str, source_url: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Scrape detailed event information from an individual event page"""
        try:
            response = requests.get(event_url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Check if this page is a blog post/list
            page_title = self._extract_title_from_html(html)
            if self._is_blog_post_list({'title': page_title, 'description': html[:1000], 'url': event_url}):
                return None
            
            # Extract event details from the page
            event = self._extract_event_from_detail_page(html, event_url, source_url)
            return event
            
        except Exception as e:
            return None
    
    def _extract_event_from_detail_page(self, html: str, event_url: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract detailed event information from an event detail page"""
        import re
        
        # Try JSON-LD first (most reliable)
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        json_ld_matches = re.finditer(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)
        for match in json_ld_matches:
            try:
                json_data = json.loads(match.group(1))
                # Handle both single objects and arrays
                if isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict) and item.get('@type') in ['Event', 'TechEvent']:
                            event = self._extract_event_from_json_ld(item, source_url)
                            if event:
                                return event
                elif isinstance(json_data, dict) and json_data.get('@type') in ['Event', 'TechEvent']:
                    event = self._extract_event_from_json_ld(json_data, source_url)
                    if event:
                        return event
            except:
                continue
        
        # Fallback: Extract from HTML structure
        title = self._extract_title_from_html(html)
        if not title:
            # Try h1 tag
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
            if h1_match:
                title = h1_match.group(1).strip()
        
        if not title:
            return None
        
        # Extract description
        description = self._extract_description_from_detail_page(html)
        
        # Extract date (multiple patterns)
        date_str = self._extract_date_from_detail_page(html, title)
        if not date_str:
            return None  # Must have a date
        
        # Validate date format and sanity check
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Sanity check: date should be between 2020 and 2030
            if date_obj.year < 2020 or date_obj.year > 2030:
                return None  # Invalid year (catches dates like 3105-07-02)
        except ValueError:
            return None  # Invalid date format
        
        # Only future events
        if not self.date_extractor.is_future_event(date_str, date_str):
            return None
        
        # Check if it's tech-related
        combined = f"{title} {description}".lower()
        has_tech = any(keyword.lower() in combined for keyword in self.tech_keywords)
        has_event = any(keyword.lower() in combined for keyword in self.event_keywords)
        
        if not (has_tech and has_event):
            return None  # Not a relevant tech event
        
        # IMPORTANT: Only include events that are Boston local OR virtual (user requirement)
        location = self._extract_tech_location_from_content(html)
        location_lower = location.lower()
        is_virtual = self._is_virtual_event(html)
        combined_location = f"{title} {description} {location}".lower()
        
        # Case-insensitive Boston check
        is_boston = any(b.lower() in combined_location for b in self.boston_keywords)
        is_virt = is_virtual or any(v in combined_location for v in self.virtual_keywords)
        
        # Reject if not Boston and not virtual
        if not (is_boston or is_virt):
            return None  # Not Boston local or virtual - skip
        
        event = {
            'title': title,
            'description': description[:500],
            'url': event_url,
            'source_url': source_url,
            'is_virtual': self._is_virtual_event(html),
            'requires_registration': 'register' in html.lower() or 'rsvp' in html.lower(),
            'categories': self._extract_tech_categories(title),
            'host': self._extract_host_from_url(source_url),
            'cost_type': self._determine_cost_type(html),
            'date': date_str,
            'time': self.date_extractor.extract_event_time(title, html),
            'location': self._extract_tech_location_from_content(html),
            'source': 'Customized'
        }
        
        return event
    
    def _extract_description_from_detail_page(self, html: str) -> str:
        """Extract event description from detail page"""
        import re
        import html as html_module
        
        # Try meta description first
        meta_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html, re.IGNORECASE)
        if meta_match:
            desc = meta_match.group(1).strip()
            # Clean meta description too
            try:
                desc = html_module.unescape(desc)
            except:
                pass
            # Remove JSON-like patterns
            desc = re.sub(r'[a-zA-Z_]+="[^"]*"', ' ', desc)
            desc = re.sub(r'"[a-zA-Z_]+":"[^"]*"', ' ', desc)
            # Check if it's garbage
            if len(desc) > 0:
                alphanumeric_chars = sum(1 for c in desc if c.isalnum())
                if alphanumeric_chars / len(desc) >= 0.5:  # At least 50% alphanumeric
                    return desc[:500]
            # If garbage, fall through to other extraction methods
        
        # Try JSON-LD description
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        json_ld_matches = re.finditer(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)
        for match in json_ld_matches:
            try:
                json_data = json.loads(match.group(1))
                if isinstance(json_data, dict):
                    desc = json_data.get('description', '')
                    if desc:
                        return desc[:500]
                elif isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict):
                            desc = item.get('description', '')
                            if desc:
                                return desc[:500]
            except:
                continue
        
        # Try common content containers
        content_patterns = [
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</p>',
        ]
        
        import html as html_module
        
        for pattern in content_patterns:
            matches = re.finditer(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                text = match.group(1)
                
                # Remove script and style tags
                text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
                
                # Remove all HTML tags
                text = re.sub(r'<[^>]+>', ' ', text)
                
                # Decode HTML entities
                try:
                    text = html_module.unescape(text)
                except:
                    pass
                
                # Remove JavaScript/JSON-like patterns (more aggressive)
                text = re.sub(r'data-[a-z-]+="[^"]*"', ' ', text, flags=re.IGNORECASE)
                text = re.sub(r'data-[a-z-]+=\'[^\']*\'', ' ', text, flags=re.IGNORECASE)
                text = re.sub(r'\{"[^"]+":"[^"]+"\}', ' ', text)  # JSON objects
                text = re.sub(r'\{[^}]*"id":"[^"]+"[^}]*\}', ' ', text)  # More JSON patterns
                text = re.sub(r'aria-[a-z-]+="[^"]*"', ' ', text, flags=re.IGNORECASE)
                text = re.sub(r'[a-z-]+="[^"]*"', ' ', text, flags=re.IGNORECASE)  # Remove any remaining HTML attributes
                # Remove patterns like 'id":"n1c1c5c8c3m1r1a1"
                text = re.sub(r'"id":"[^"]*"', ' ', text)
                text = re.sub(r'"sN":[0-9]+', ' ', text)
                text = re.sub(r'"aN":"[^"]*"', ' ', text)
                text = re.sub(r'"cN":"[^"]*"', ' ', text)
                text = re.sub(r'"cT":"[^"]*"', ' ', text)
                # Remove Microsoft navigation patterns like :"CatNav_Microsoft 365_nav"
                text = re.sub(r':"[A-Z][a-zA-Z0-9_ ]+[Nn]av"', ' ', text)  # CatNav, nav patterns
                text = re.sub(r':"[A-Z][a-zA-Z_]+"', ' ', text)
                text = re.sub(r':"[^"]*_[^"]*"', ' ', text)
                # Remove colon-quote patterns (Microsoft navigation attributes)
                text = re.sub(r':"[^"]*"', ' ', text)  # Any :"something"
                
                # Remove any remaining JSON/attribute-like patterns
                text = re.sub(r'"[a-zA-Z_]+":"[^"]*"', ' ', text)
                text = re.sub(r'[a-zA-Z_]+="[^"]*"', ' ', text)
                text = re.sub(r'[a-zA-Z_]+=\'[^\']*\'', ' ', text)
                
                # Remove ID-like sequences
                text = re.sub(r'\b[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+\b', ' ', text)
                
                # Clean up whitespace
                text = ' '.join(text.split())
                
                # Remove strings that are mostly symbols (likely code/garbage)
                words = text.split()
                if len(words) > 0:
                    non_word_ratio = sum(1 for w in words if not re.match(r'^[a-zA-Z0-9\s\.,;:!?\-]+$', w)) / len(words)
                    if non_word_ratio > 0.3:
                        continue  # Skip this match, try next
                    
                    # Check for JSON-like patterns
                    json_like_patterns = len(re.findall(r'"[^"]*":"[^"]*"', text))
                    if json_like_patterns > 2:
                        continue  # Too many JSON patterns
                
                # Final check: alphanumeric ratio
                if len(text) > 0:
                    alphanumeric_chars = sum(1 for c in text if c.isalnum())
                    if alphanumeric_chars / len(text) < 0.5:
                        continue  # Too many special characters
                
                if len(text) > 50:  # Meaningful description
                    return text[:500]
        
        return ''
    
    def _extract_date_from_detail_page(self, html: str, title: str) -> str:
        """Extract date from event detail page"""
        import re
        
        # Try JSON-LD first
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        json_ld_matches = re.finditer(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)
        for match in json_ld_matches:
            try:
                json_data = json.loads(match.group(1))
                if isinstance(json_data, dict):
                    start_date = json_data.get('startDate', '')
                    if start_date:
                        date_str = self.date_extractor.extract_event_date(start_date, '')
                        if date_str:
                            return date_str
                elif isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict):
                            start_date = item.get('startDate', '')
                            if start_date:
                                date_str = self.date_extractor.extract_event_date(start_date, '')
                                if date_str:
                                    return date_str
            except:
                continue
        
        # Try common date patterns in HTML
        date_patterns = [
            r'<time[^>]*datetime="([^"]+)"',
            r'<time[^>]*>([^<]+)</time>',
            r'class="[^"]*date[^"]*"[^>]*>([^<]+)',
            r'id="[^"]*date[^"]*"[^>]*>([^<]+)',
            r'(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                extracted = self.date_extractor.extract_event_date(date_str, '')
                if extracted and self.date_extractor.is_future_event(extracted, extracted):
                    return extracted
        
        # Last resort: try title
        return self.date_extractor.extract_event_date(title, html) or ''
    
    def _extract_title_from_html(self, html: str) -> str:
        """Extract page title from HTML"""
        import re
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return ""
    
    def _extract_date_from_context(self, context: str) -> str:
        """Extract date from HTML context"""
        # Common date patterns in HTML
        date_patterns = [
            r'(\w+\s+\d{1,2},?\s+\d{4})',  # January 15, 2026
            r'(\d{1,2}/\d{1,2}/\d{4})',     # 1/15/2026
            r'(\d{4}-\d{2}-\d{2})',         # 2026-01-15
            r'datetime="([^"]+)"',          # <time datetime="...">
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                extracted = self.date_extractor.extract_event_date(date_str, '')
                if extracted and self.date_extractor.is_future_event(extracted, extracted):
                    return extracted
        
        return ''
    
    def _extract_description_from_html(self, html_context: str) -> str:
        """Extract description from HTML context - clean text extraction"""
        import re
        import html as html_module
        
        # Remove script and style tags completely
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', html_context, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        try:
            text = html_module.unescape(text)
        except:
            pass
        
        # Remove JavaScript/JSON-like patterns (data-m attributes, etc.) - more aggressive
        text = re.sub(r'data-[a-z-]+="[^"]*"', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'data-[a-z-]+=\'[^\']*\'', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\{"[^"]+":"[^"]+"\}', ' ', text)  # Remove JSON-like strings
        text = re.sub(r'\{[^}]*"id":"[^"]+"[^}]*\}', ' ', text)  # More JSON patterns
        text = re.sub(r'aria-[a-z-]+="[^"]*"', ' ', text, flags=re.IGNORECASE)
        
        # Remove common HTML attribute patterns
        text = re.sub(r'[a-z-]+="[^"]*"', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'class="[^"]*"', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'id="[^"]*"', ' ', text, flags=re.IGNORECASE)
        # Remove patterns like "id":"n1c1c5c8c3m1r1a1" and other JSON-like patterns
        text = re.sub(r'"id":"[^"]*"', ' ', text)
        text = re.sub(r'"sN":[0-9]+', ' ', text)
        text = re.sub(r'"aN":"[^"]*"', ' ', text)
        text = re.sub(r'"cN":"[^"]*"', ' ', text)
        text = re.sub(r'"cT":"[^"]*"', ' ', text)
        # Remove Microsoft navigation patterns like :"CatNav_Microsoft 365_nav"
        text = re.sub(r':"[A-Z][a-zA-Z0-9_ ]+[Nn]av"', ' ', text)  # CatNav, nav patterns
        text = re.sub(r':"[A-Z][a-zA-Z_]+"', ' ', text)
        text = re.sub(r':"[^"]*_[^"]*"', ' ', text)  # Remove underscore patterns
        # Remove colon-quote patterns (Microsoft navigation attributes)
        text = re.sub(r':"[^"]*"', ' ', text)  # Any :"something"
        
        # Remove any remaining JSON/attribute-like patterns
        text = re.sub(r'"[a-zA-Z_]+":"[^"]*"', ' ', text)  # Any "key":"value"
        text = re.sub(r'[a-zA-Z_]+="[^"]*"', ' ', text)  # Any key="value"
        text = re.sub(r'[a-zA-Z_]+=\'[^\']*\'', ' ', text)  # Any key='value'
        
        # Remove sequences that look like IDs or codes
        text = re.sub(r'\b[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+[a-z][0-9]+\b', ' ', text)  # Pattern like n1c6c2c7c8c3m1r1a1
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Remove strings that are mostly symbols/numbers (likely code)
        words = text.split()
        if len(words) > 0:
            # If more than 30% are non-word characters, it's likely garbage
            non_word_ratio = sum(1 for w in words if not re.match(r'^[a-zA-Z0-9\s\.,;:!?\-]+$', w)) / len(words)
            if non_word_ratio > 0.3:
                return ''  # Too much garbage, skip
            
            # Also check if description contains too many JSON-like patterns
            json_like_patterns = len(re.findall(r'"[^"]*":"[^"]*"', text))
            if json_like_patterns > 2:
                return ''  # Too many JSON patterns, likely garbage
        
        # Final check: if description is mostly special characters/IDs, skip it
        if len(text) > 0:
            alphanumeric_chars = sum(1 for c in text if c.isalnum())
            if alphanumeric_chars / len(text) < 0.5:  # Less than 50% alphanumeric
                return ''  # Too many special characters
        
        # Return first 300 characters of clean text
        return text[:300] if text else ''
    
    def _extract_host_from_url(self, url: str) -> str:
        """Extract host organization from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            # Known hosts
            if 'nvidia' in domain:
                return 'NVIDIA'
            elif 'microsoft' in domain:
                return 'Microsoft'
            elif 'gdg' in domain or 'google' in domain:
                return 'Google'
            elif 'aicamp' in domain:
                return 'AI Camp'
            else:
                # Extract company name from domain
                parts = domain.split('.')
                if len(parts) > 1:
                    return parts[0].capitalize()
                return 'Other'
        except:
            return 'Other'
    
    def _extract_event_from_json_ld(self, json_data: Dict[str, Any], source_url: str) -> Optional[Dict[str, Any]]:
        """Extract event from JSON-LD structured data"""
        try:
            name = json_data.get('name', '')
            if not name:
                return None
            
            start_date = json_data.get('startDate', '')
            if start_date:
                date_str = self.date_extractor.extract_event_date(start_date, '')
                if not date_str or not self.date_extractor.is_future_event(date_str, date_str):
                    return None
            else:
                return None  # Must have a date
            
            event = {
                'title': name,
                'description': json_data.get('description', '')[:500],
                'url': json_data.get('url', source_url),
                'source_url': source_url,
                'is_virtual': json_data.get('eventAttendanceMode', '').lower() == 'online',
                'requires_registration': True,
                'categories': self._extract_tech_categories(name),
                'host': self._extract_host_from_url(source_url),
                'cost_type': self._determine_cost_type(json_data.get('description', '')),
                'date': date_str,
                'time': self.date_extractor.extract_event_time(start_date, ''),
                'location': json_data.get('location', {}).get('name', 'Virtual' if json_data.get('eventAttendanceMode') == 'Online' else 'TBD'),
                'source': 'Customized'
            }
            return event
        except Exception as e:
            return None
    
    def _is_blog_post_list(self, event: Dict[str, Any]) -> bool:
        """Filter out blog posts that are lists of events (e.g., 'top 10 conferences')"""
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        url = event.get('url', '').lower()
        
        # Filter out navigation/account pages
        navigation_patterns = [
            'upcoming events', 'past events', 'all events', 'my events',
            'log in', 'login', 'sign up', 'signup', 'register', 'register now',
            'create account', 'my account', 'account settings',
            'home', 'about', 'contact', 'help', 'faq',
            'upcoming', 'past', 'events list', 'events page',
            'meet the team', 'travel funding', 'sponsors', 'speakers',
            'venue', 'hotel', 'accommodation', 'registration',
            'buy tickets', 'purchase tickets',
            'load more', 'see more', 'show more', 'view more', 'view all',
            'next page', 'previous page', 'page', 'pagination'
        ]
        
        if any(pattern in title for pattern in navigation_patterns):
            return True
        
        # Filter out single-word titles that are likely categories/navigation (unless they have event keywords)
        # Titles like "AI", "Security", "Devices" are likely category pages
        title_words = title.split()
        if len(title_words) <= 2 and not any(ev in title for ev in ['event', 'workshop', 'webinar', 'conference', 'summit', 'meetup', 'training', 'seminar', 'hackathon']):
            # But allow if description is substantial (real events have descriptions)
            if len(description) < 100:
                return True
        
        # Filter out very generic category-like titles
        generic_categories = [
            'ai', 'security', 'devices', 'infrastructure', 'productivity',
            'developer tools', 'data and analytics', 'business applications',
            'industry focused', 'industry events', 'other professionals',
            'students and education', 'decision-makers', 'executives',
            'it professionals', 'partners', 'code of conduct',
            'english (united states)', 'dynamics 365', 'microsoft 365',
            'microsoft copilot', 'microsoft fabric', 'microsoft power platform',
            'microsoft security', 'power bi', 'surface', 'windows',
            'windows server', 'github'
        ]
        
        # If title is exactly one of these generic categories, it's likely not an event
        if title.strip() in generic_categories:
            return True
        
        # Filter out account/login/profile URLs
        if any(pattern in url for pattern in ['/login', '/logout', '/account', '/accounts/', '/profile', '/settings', '/admin']):
            return True
        
        combined = f"{title} {description} {url}"
        
        # Blog post/list indicators - expanded to catch more patterns
        blog_post_patterns = [
            r'top \d+',  # "Top 7", "Top 10"
            r'\d+ best',  # "7 best", "10 best"
            r'\d+ must.*attend',
            r'\d+ .* (to|you) (attend|know|check)',
            r'list of',
            r'guide to',
            r'how to (find|choose|pick|select)',
            r'ultimate (guide|list)',
            r'complete (guide|list)',
            r'everything you need to know',
            r'(our|your) (guide|list|roundup)',
            r'roundup of',
            r'compilation of',
            r'\d+ (events|conferences|workshops|courses|trainings) (to|you|for)',
            r'(article|blog|post)',
            r'/blog/',
            r'/article/',
            r'/news/',
            r'/posts/',
            r'online courses? (for|in)',  # "Online Courses for 2025"
            r'courses? (for|in) \d{4}',  # "Courses for 2025-2026"
            r'\d+ .* courses?',  # "7 Cloud Computing Courses"
            r'recommended .* courses?',
            r'best .* courses?',
            r'(free|paid) .* courses? (to|for|in)',
            r'\.(com|org)/blog',  # URLs with /blog
            r'\.(com|org)/article',  # URLs with /article
        ]
        
        # Check title patterns first (most reliable)
        for pattern in blog_post_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        
        # Check for list-like structures in description
        list_indicators = [
            r'\d+\.\s+[A-Z]',  # Numbered list: "1. Event", "2. Event"
            r'#\d+',           # Hash numbered
            r'(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)',
        ]
        
        # If description contains many numbered items, likely a list
        numbered_items = len(re.findall(r'\d+\.\s+', description))
        if numbered_items >= 3:
            return True
        
        # Check URL patterns
        blog_url_patterns = ['/blog/', '/article/', '/news/', '/posts/', '/editorial/']
        if any(pattern in url for pattern in blog_url_patterns):
            return True
        
        return False
    
    def _is_valid_location(self, event: Dict[str, Any]) -> bool:
        """Validate that event is Boston local or Virtual (exclude other cities)"""
        title = event.get('title', '').lower()
        description = event.get('description', '').lower()
        location = event.get('location', '').lower()
        is_virtual = event.get('is_virtual', False)
        
        combined = f"{title} {description} {location}"
        title_lower = title.lower()
        location_lower = location.lower()
        
        # Exclude specific non-Boston cities and regions FIRST (before Boston check)
        excluded_locations = [
            # US cities (non-Boston)
            'chicago', 'nyc', 'new york', 'san francisco', 'sf', 'los angeles', 'la',
            'seattle', 'austin', 'denver', 'atlanta', 'miami', 'dallas', 'houston',
            'philadelphia', 'philly', 'washington dc', 'dc', 'baltimore', 'detroit',
            'minneapolis', 'portland', 'san diego', 'phoenix', 'nashville', 'orlando',
            'tampa', 'raleigh', 'charlotte', 'indianapolis', 'columbus', 'cleveland',
            'cincinnati', 'pittsburgh', 'kansas city', 'st. louis', 'new orleans',
            'vegas', 'las vegas', 'san jose', 'oakland', 'sacramento', 'fresno',
            # International regions
            'japan', 'tokyo', 'osaka', 'kyoto', 'yokohama',
            'europe', 'london', 'paris', 'berlin', 'amsterdam', 'barcelona', 'madrid',
            'rome', 'milan', 'vienna', 'zurich', 'stockholm', 'copenhagen',
            'asia', 'singapore', 'hong kong', 'seoul', 'beijing', 'shanghai',
            'india', 'mumbai', 'delhi', 'bangalore', 'hyderabad',
            'australia', 'sydney', 'melbourne',
            'canada', 'toronto', 'vancouver', 'montreal',
            'mexico', 'mexico city',
            'brazil', 'sao paulo',
            # Common country codes/names
            'jp', 'jpn', 'uk', 'gbr', 'de', 'deu', 'fr', 'fra', 'es', 'esp',
            'it', 'ita', 'nl', 'nld', 'se', 'swe', 'dk', 'dnk', 'au', 'aus',
            'ca', 'can', 'mx', 'mex', 'br', 'bra', 'in', 'ind', 'kr', 'kor',
            'cn', 'chn', 'sg', 'sgp', 'hk', 'hkg'
        ]
        
        # If title mentions excluded location AND it's not clearly virtual, reject it
        title_mentions_excluded = False
        for excluded in excluded_locations:
            if re.search(rf'\b{re.escape(excluded)}\b', title_lower):
                title_mentions_excluded = True
                break
        
        # If title mentions excluded location, it must be clearly virtual to pass
        if title_mentions_excluded:
            # Check if it's clearly virtual in title or location
            is_clearly_virtual = (is_virtual or 
                                'virtual' in title_lower or 'online' in title_lower or
                                'virtual' in location_lower or 'online' in location_lower or
                                location_lower in ['virtual', 'online', 'remote'])
            if not is_clearly_virtual:
                return False  # Title mentions non-US location but not virtual
        
        # If explicitly virtual/online (and didn't fail above), allow it
        if is_virtual or 'virtual' in combined or 'online' in combined:
            return True
        
        # Check for excluded locations (be more strict - if title/location mentions them, reject)
        # But allow if it's clearly virtual/online
        if not (is_virtual or 'virtual' in combined or 'online' in combined):
            # Check title and location fields specifically (already defined above)
            desc_lower = description.lower()
            
            # Check for country/region mentions in title or location (STRICT CHECK)
            for excluded in excluded_locations:
                # Check if excluded location appears in title or location field
                # Use word boundaries to avoid false positives (e.g., "japan" in "japanese" but not "Japan" as location)
                title_has_location = re.search(rf'\b{re.escape(excluded)}\b', title_lower)
                location_has_location = re.search(rf'\b{re.escape(excluded)}\b', location_lower)
                
                if title_has_location or location_has_location:
                    return False  # Reject if in title or location (strict - no exceptions)
        
        # Also check for explicit location patterns like "| Japan", "in Europe", etc.
        location_patterns = [
            r'\|\s*(japan|jpn|europe|asia|uk|germany|france|spain|italy|netherlands|sweden|denmark|australia|canada|mexico|brazil|india|korea|china|singapore|hong kong)',
            r'in\s+(japan|europe|asia|uk|germany|france|spain|italy|netherlands|sweden|denmark|australia|canada|mexico|brazil|india|korea|china|singapore|hong kong)',
            r'\b(japan|europe|asia|uk|germany|france|spain|italy|netherlands|sweden|denmark|australia|canada|mexico|brazil|india|korea|china|singapore|hong kong)\s+\|',
        ]
        
        if not (is_virtual or 'virtual' in combined or 'online' in combined):
            for pattern in location_patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return False
        
        # Check for Boston keywords (case-insensitive)
        boston_found = any(b.lower() in combined for b in self.boston_keywords)
        if boston_found:
            return True
        
        # If we can't determine Boston or Virtual, and location is specified, reject
        # (Better to be conservative)
        if location and location not in ['virtual', 'online', 'remote', '']:
            # Check if location contains Boston keywords (case-insensitive)
            location_has_boston = any(b.lower() in location for b in self.boston_keywords)
            # Also check combined text for Boston (location might just say "MA" or similar)
            combined_has_boston = any(b.lower() in combined for b in self.boston_keywords)
            
            if not location_has_boston and not combined_has_boston:
                # Unless it's clearly a virtual indicator
                if not any(v in location for v in ['virtual', 'online', 'remote', 'webinar', 'zoom', 'teams']):
                    return False
        
        # Default: allow if no conflicting location info
        return True
    
    def _meets_tech_criteria(self, result: Dict[str, Any]) -> bool:
        """Check if search result meets tech event criteria - focused on free workshops/webinars/trainings"""
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        url = result.get('url', '').lower()
        combined_text = f"{title} {content} {url}"
        
        # EXCLUDE commercial conferences (paid, multi-day, expensive)
        commercial_exclusion_keywords = [
            'ticket price', 'registration fee', '$', '€', '£', 'cost:', 'price:',
            'early bird', 'super early', 'pass', 'expo', 'exhibition', 'sponsor',
            '3-day', '4-day', '5-day', 'week-long', 'multi-day conference',
            'luxury', 'hotel', 'resort', 'venue fee'
        ]
        if any(keyword in combined_text for keyword in commercial_exclusion_keywords):
            # But allow if explicitly marked as free
            if 'free' not in combined_text and 'complimentary' not in combined_text and 'no cost' not in combined_text:
                return False
        
        # PRIORITIZE: workshops, webinars, trainings, meetups, hackathons (hands-on)
        preferred_event_types = [
            'workshop', 'webinar', 'training', 'bootcamp', 'tutorial', 'hands-on',
            'meetup', 'hackathon', 'coding challenge', 'hands-on session', 'lab',
            'one-day', 'one day', 'half-day', 'half day', 'developer day', 'tech day',
            # Casual event types
            'coding night', 'dev night', 'tech talk', 'code review',
            'pair programming', 'mob programming', 'TDD', 'code kata',
            'lightning talk', 'tech lunch', 'brown bag', 'office hours'
        ]
        has_preferred_type = any(event_type in combined_text for event_type in preferred_event_types)
        
        # EXCLUDE: large commercial conferences, summits (unless explicitly free/one-day)
        exclude_types = ['summit', 'expo', 'convention', 'forum']
        if any(exclude_type in combined_text for exclude_type in exclude_types):
            # Only allow if explicitly marked as free AND (workshop OR one-day)
            if 'free' not in combined_text or (not has_preferred_type and 'one-day' not in combined_text and 'one day' not in combined_text):
                return False
        
        # Must be tech-related
        has_tech = any(keyword.lower() in combined_text for keyword in self.tech_keywords)
        
        # Must be an event type
        has_event = any(keyword.lower() in combined_text for keyword in self.event_keywords)
        
        # PRIORITIZE: Must be FREE (or explicitly mention it's free)
        is_free = any(keyword in combined_text for keyword in ['free', 'complimentary', 'no cost', 'gratis', 'no charge'])
        
        # Must be in Boston area OR virtual
        has_location = (any(keyword.lower() in combined_text for keyword in self.boston_keywords) or
                       any(keyword.lower() in combined_text for keyword in self.virtual_keywords))
        
        # Must be in the future
        # Try to get date from result if available
        event_date = result.get('date', '') if isinstance(result, dict) else ''
        is_future_event = self._is_future_event(combined_text, event_date)
        
        # Prioritize: free + preferred type + tech + location + future
        # Allow non-free only if it's a preferred hands-on type
        if is_free and has_preferred_type:
            return has_tech and has_event and has_location and is_future_event
        elif has_preferred_type:
            # Allow paid workshops/trainings if explicitly hands-on
            return has_tech and has_event and has_location and is_future_event
        else:
            # For other events, only if explicitly free
            return is_free and has_tech and has_event and has_location and is_future_event
    
    def _is_future_event(self, text: str, event_date: str = None) -> bool:
        """Check if event is in the future"""
        from datetime import datetime
        import re
        
        # First, check if we have an actual date - this is the most reliable
        if event_date:
            try:
                event_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
                today = datetime.now().date()
                if event_dt >= today:
                    return True
                else:
                    return False  # If date is provided and in past, definitely not future
            except:
                pass  # If date parsing fails, fall back to text analysis
        
        # Check for explicit future keywords
        has_future_keywords = any(keyword in text.lower() for keyword in [
            'upcoming', 'future', 'next', 'tomorrow', 'this week', 'this month'
        ])
        
        # Check for current and future years
        current_year = datetime.now().year
        future_years = [str(current_year), str(current_year + 1), str(current_year + 2)]
        has_future_years = any(year in text for year in future_years)
        
        # Check for specific future dates
        month_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}',
        ]
        
        has_future_dates = any(re.search(pattern, text, re.IGNORECASE) for pattern in month_patterns)
        
        # Check for "today" or "tonight"
        has_today = any(word in text.lower() for word in ['today', 'tonight', 'this evening'])
        
        return has_future_keywords or has_future_years or has_future_dates or has_today
    
    def _extract_tech_event_from_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract tech event information from search result with improved free/workshop detection"""
        try:
            title = result.get('title', '').strip()
            url = result.get('url', '')
            content = result.get('content', '')
            
            if not title or not url:
                return None
            
            combined_text = f"{title} {content}".lower()
            
            # Check if this is likely a free workshop/webinar/training (priority events)
            is_likely_free_workshop = any(keyword in combined_text for keyword in [
                'free workshop', 'free webinar', 'free training', 'free bootcamp',
                'free tutorial', 'free meetup', 'free hackathon', 'complimentary workshop',
                'no cost workshop', 'no charge webinar'
            ])
            
            # Better cost detection - prioritize free mentions
            cost_type = self._determine_cost_type(content)
            if is_likely_free_workshop and cost_type != 'Free':
                cost_type = 'Free'  # Override if explicitly mentioned as free
            
            # Extract event details
            event = {
                'title': title,
                'url': url,
                'description': content[:500] + '...' if len(content) > 500 else content,
                'source_url': url,
                'is_virtual': self._is_virtual_event(content),
                'requires_registration': self._requires_registration(content),
                'categories': self._extract_tech_categories(title),
                'host': self._extract_tech_host_from_url(url),
                'cost_type': cost_type,
                'date': self.date_extractor.extract_event_date(title, content),
                'time': self.date_extractor.extract_event_time(title, content),
                'location': self._extract_tech_location_from_content(content),
                'source': 'Tavily'
            }
            
            # Skip if no valid date extracted
            if not event.get('date'):
                return None
            
            return event
            
        except Exception as e:
            print(f"Error extracting tech event from result: {e}")
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
    
    def _extract_tech_host_from_url(self, url: str) -> str:
        """Extract tech company host from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Known tech hosts mapping
            host_mapping = {
                'google.com': 'Google',
                'microsoft.com': 'Microsoft',
                'aws.amazon.com': 'Amazon Web Services',
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
                'stripe.com': 'Stripe',
                'square.com': 'Square',
                'paypal.com': 'PayPal',
                'shopify.com': 'Shopify',
                'twilio.com': 'Twilio',
                'sendgrid.com': 'SendGrid',
                'mailchimp.com': 'Mailchimp',
                'hubspot.com': 'HubSpot',
                'workday.com': 'Workday',
                'servicenow.com': 'ServiceNow',
                'zendesk.com': 'Zendesk',
                'meetup.com': 'Meetup',
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
            
            return 'Tech Community'
            
        except Exception:
            return 'Tech Community'
    
    def _extract_tech_location_from_content(self, content: str) -> str:
        """Extract location from content"""
        content_lower = content.lower()
        
        # Check for virtual events first
        if any(keyword in content_lower for keyword in self.virtual_keywords):
            return 'Virtual'
        
        # Look for Boston area locations
        for location in self.boston_keywords:
            if location.lower() in content_lower:
                return location
        
        return 'Virtual'  # Default to virtual for tech events
    
    def _determine_cost_type(self, content: str) -> str:
        """Determine if event is free or paid - improved detection"""
        content_lower = content.lower()
        
        # Strong free indicators (check first)
        strong_free_keywords = [
            'free', 'complimentary', 'gratis', 'no cost', 'no charge', 
            'no fee', 'free admission', 'free entry', 'free to attend',
            'free registration', 'free workshop', 'free webinar', 'free training'
        ]
        has_free = any(keyword in content_lower for keyword in strong_free_keywords)
        
        # Paid indicators (but check for exceptions)
        paid_keywords = ['cost', 'price', 'fee', 'ticket', 'buy', 'purchase', '$', 'paid', 'charge']
        has_paid_keywords = any(keyword in content_lower for keyword in paid_keywords)
        
        # Exceptions: "free ticket", "no cost", etc. override paid keywords
        if has_free:
            # Check if it's "free" but actually mentions pricing elsewhere
            if '$' in content_lower or 'price:' in content_lower or 'cost:' in content_lower:
                # Look for context - is it "free for students" but paid for others?
                if 'student' in content_lower or 'member' in content_lower:
                    return 'Free (with conditions)'
                # Check if free is mentioned prominently
                free_pos = content_lower.find('free')
                if free_pos != -1 and free_pos < 200:  # Free mentioned early
                    return 'Free'
            else:
                return 'Free'
        
        # Check for specific paid amounts
        if '$' in content_lower or 'price:' in content_lower:
            return 'Paid'
        
        # If has paid keywords but no explicit free, likely paid
        if has_paid_keywords:
            return 'Paid'
        
        # Default for workshops/meetups/webinars - assume free unless stated otherwise
        workshop_types = ['workshop', 'meetup', 'webinar', 'training', 'bootcamp']
        if any(wt in content_lower for wt in workshop_types):
            return 'Free (likely)'
        
        return 'Unknown'
    
    
    def _extract_event_date_from_rss(self, entry) -> str:
        """Extract actual event date from RSS entry (not publication date)"""
        title = entry.get('title', '')
        description = entry.get('description', '')
        link = entry.get('link', '')
        
        # First, try to extract date from title/description using improved extractor
        event_date = self.date_extractor.extract_event_date(title, description)
        if event_date:
            return event_date
        
        # For Meetup RSS feeds, try to get date from the event page
        if 'meetup.com' in link and '/events/' in link:
            try:
                # Fetch the event page to extract the actual event date
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                response = requests.get(link, headers=headers, timeout=10)
                if response.status_code == 200:
                    html = response.text
                    
                    # Look for date patterns in the HTML
                    # Meetup typically shows dates like "Monday, January 15, 2026"
                    import re
                    date_patterns = [
                        r'(\w+day,\s+\w+\s+\d{1,2},\s+\d{4})',  # Monday, January 15, 2026
                        r'(\w+\s+\d{1,2},\s+\d{4})',  # January 15, 2026
                        r'(\d{1,2}/\d{1,2}/\d{4})',  # 1/15/2026
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.findall(pattern, html)
                        for match in matches:
                            extracted = self.date_extractor.extract_event_date(match, '')
                            if extracted and self.date_extractor.is_future_event(extracted):
                                return extracted
                    
                    # Also look for time element with datetime attribute
                    time_elem = re.search(r'<time[^>]*datetime="([^"]+)"', html, re.IGNORECASE)
                    if time_elem:
                        datetime_str = time_elem.group(1)
                        # Parse ISO datetime format
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                            if dt.date() >= datetime.now().date():
                                return dt.strftime('%Y-%m-%d')
                        except:
                            pass
            except Exception as e:
                # If scraping fails, fall back to published date logic
                pass
        
        # For Meetup RSS, published date sometimes correlates with event date
        # (if it's recent and in the future)
        if 'meetup.com' in link and hasattr(entry, 'published_parsed'):
            try:
                from datetime import datetime, timedelta
                pub_date = datetime(*entry.published_parsed[:6])
                # If published within last 7 days and in the future, might be event date
                # Or if it's in the future within next 90 days, use it
                today = datetime.now().date()
                if pub_date.date() >= today and pub_date.date() <= (today + timedelta(days=90)):
                    return pub_date.strftime('%Y-%m-%d')
            except:
                pass
        
        # Fallback: if no event date found, don't return publication date
        # This prevents past events from being included
        return ''
    
    def _extract_event_time_from_rss(self, entry) -> str:
        """Extract event time from RSS entry"""
        title = entry.get('title', '')
        description = entry.get('description', '')
        
        return self.date_extractor.extract_event_time(title, description) or ''
    
    def _is_excluded_url(self, url: str) -> bool:
        """Check if URL should be excluded"""
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
            title_words = set(title.split())
            
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                if len(title_words & seen_words) / max(len(title_words), len(seen_words)) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_events.append(event)
                seen_titles.add(title)
        
        return unique_events
    
    def _filter_tech_events(self, events: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """Filter tech events to meet final criteria, prioritize free workshops/webinars/trainings"""
        filtered_events = []
        
        # First pass: Filter out blog posts/lists
        events = [e for e in events if not self._is_blog_post_list(e)]
        
        # Scoring system: prioritize free + preferred types + Boston/virtual
        def score_event(event):
            score = 0
            title = event.get('title', '').lower()
            desc = event.get('description', '').lower()
            cost = event.get('cost_type', '').lower()
            location = event.get('location', '').lower()
            source = event.get('source', '').lower()
            combined = f"{title} {desc}"
            
            # Bonus for trusted RSS sources (they're already curated)
            if 'meetup rss' in source or 'rss feed' in source or 'customized' in source:
                score += 40  # Meetup/RSS/Customized events are pre-filtered, give them a boost
            
            # High priority: free events
            if 'free' in combined or 'complimentary' in combined or cost == 'free':
                score += 100
            
            # High priority: preferred event types (workshops, webinars, trainings)
            preferred = ['workshop', 'webinar', 'training', 'bootcamp', 'tutorial', 'hands-on', 
                        'meetup', 'hackathon', 'coding challenge', 'one-day', 'one day',
                        'coding night', 'dev night', 'tech talk', 'code review',
                        'pair programming', 'TDD', 'code kata', 'lightning talk']
            if any(p in combined for p in preferred):
                score += 50
            
            # For Meetup RSS events, assume they're meetups even without keyword
            if 'meetup rss' in source:
                score += 30  # Boost for being from a tech Meetup group
            
            # Priority: Boston local events
            if any(b in location or b in combined for b in self.boston_keywords):
                score += 30
            elif location in ['ma', 'massachusetts', 'virtual'] and 'meetup rss' in source:
                score += 20  # Meetups in MA are likely Boston-area
            
            # Priority: Virtual events
            if event.get('is_virtual', False) or 'virtual' in combined or 'online' in combined:
                score += 20
            
            # Penalize: commercial conferences
            if any(exclude in combined for exclude in ['summit', 'expo', 'convention', '3-day', '4-day', '5-day']):
                if 'free' not in combined:
                    score -= 50
            
            # Less penalty for paid events from RSS (they're curated)
            if cost not in ['free', 'unknown'] and not any(p in combined for p in preferred):
                if 'meetup rss' in source or 'rss feed' in source:
                    score -= 10  # Less penalty for curated RSS
                else:
                    score -= 30
            
            return score
        
        # Score and sort events
        scored_events = [(event, score_event(event)) for event in events]
        scored_events.sort(key=lambda x: x[1], reverse=True)
        
        # Separate events by source to ensure representation
        rss_events_scored = [(e, s) for e, s in scored_events if e.get('source', '').lower() in ['meetup rss', 'tech rss feed', 'eventbrite', 'customized']]
        tavily_events_scored = [(e, s) for e, s in scored_events if e.get('source', '').lower() == 'tavily']
        
        # Reserve slots: 50% for RSS/Eventbrite/Customized, 50% for Tavily
        # Increased to ensure Customized events are well represented
        rss_slots = max(20, int(max_results * 0.5))
        tavily_slots = max_results - rss_slots
        
        # First, add RSS/Eventbrite/Customized events (prioritize curated sources)
        # Process Customized events first to ensure they get included
        customized_events = [(e, s) for e, s in rss_events_scored if e.get('source', '').lower() == 'customized']
        other_rss_events = [(e, s) for e, s in rss_events_scored if e.get('source', '').lower() != 'customized']
        
        # Process Customized first
        for event, score in customized_events:
            if len(filtered_events) >= max_results:
                break
            if len([e for e in filtered_events if e.get('source', '').lower() in ['meetup rss', 'tech rss feed', 'eventbrite', 'customized']]) >= rss_slots:
                break
            # Final validation
            if (self._is_excluded_url(event.get('url', '')) or 
                self._is_blog_post_list(event) or
                not self._is_future_event(f"{event.get('title', '')} {event.get('description', '')}", event.get('date')) or
                not self._is_valid_location(event)):
                continue
            filtered_events.append(event)
        
        # Then add other RSS/Eventbrite events
        for event, score in other_rss_events:
            if len(filtered_events) >= max_results:
                break
            if len([e for e in filtered_events if e.get('source', '').lower() in ['meetup rss', 'tech rss feed', 'eventbrite', 'customized']]) >= rss_slots:
                break
            # Final validation
            if (self._is_excluded_url(event.get('url', '')) or 
                self._is_blog_post_list(event) or
                not self._is_future_event(f"{event.get('title', '')} {event.get('description', '')}", event.get('date')) or
                not self._is_valid_location(event)):
                continue
            filtered_events.append(event)
        
        # Then, add Tavily events
        for event, score in tavily_events_scored:
            if len(filtered_events) >= max_results:
                break
            # Final validation
            if (self._is_excluded_url(event.get('url', '')) or 
                self._is_blog_post_list(event) or
                not self._is_future_event(f"{event.get('title', '')} {event.get('description', '')}", event.get('date')) or
                not self._is_valid_location(event)):
                continue
            # Only accept events with positive scores (unless we need more)
            if score < -20 and len(filtered_events) >= max_results // 2:
                continue
            filtered_events.append(event)
        
        return filtered_events
    
    def _clean_description(self, description: str) -> str:
        """Clean description text to remove JSON/HTML gibberish - final cleanup"""
        if not description:
            return ''
        
        import re
        import html as html_module
        
        text = description
        
        # Remove Microsoft navigation patterns (more comprehensive)
        # Patterns like :"CatNav_Microsoft 365_nav" or Training_nav"
        text = re.sub(r':"[^"]*[Nn]av"', ' ', text)
        text = re.sub(r'[A-Za-z]+_[A-Za-z0-9 ]+_nav"', ' ', text)  # CatNav_Product_nav" or Training_nav"
        text = re.sub(r'data-m=\'\{[^\']*\}\'', ' ', text)
        text = re.sub(r'data-m="\{[^"]*\}"', ' ', text)
        
        # Remove all JSON-like patterns (more aggressive)
        text = re.sub(r'"[a-zA-Z_]+":"[^"]*"', ' ', text)  # "key":"value"
        text = re.sub(r'"[a-zA-Z_]+":\d+', ' ', text)  # "key":123
        text = re.sub(r':"[^"]*"', ' ', text)  # :"anything"
        text = re.sub(r'\{[^}]*"[a-zA-Z_]+":"[^"]*"[^}]*\}', ' ', text)  # {JSON objects}
        
        # Remove ID patterns like n1c6c2c7c8c3m1r1a1 (more flexible)
        text = re.sub(r'\b[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+\b', ' ', text)
        text = re.sub(r'\b[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+\b', ' ', text)  # Shorter patterns too
        
        # Remove patterns like ", , , }" or ", , , '}" (leftover from JSON cleaning)
        text = re.sub(r',\s*,\s*,', ' ', text)  # Multiple commas
        text = re.sub(r'^[,}\s]+', '', text)  # Leading commas/braces
        text = re.sub(r'[,}\s]+$', '', text)  # Trailing commas/braces
        
        # Remove HTML tags if any remain (more aggressive)
        text = re.sub(r'<[^>]+>', ' ', text)
        # Also remove HTML tag-like fragments that might remain
        text = re.sub(r'<[a-z]+[^>]*', ' ', text)  # Opening tags without closing
        text = re.sub(r'</[a-z]+>', ' ', text)  # Closing tags
        # Remove common HTML attributes/class patterns
        text = re.sub(r'class="[^"]*"', ' ', text)
        text = re.sub(r'js-[a-z-]+', ' ', text)  # Remove js-nav-menu, js-*, etc.
        
        # Decode HTML entities
        try:
            text = html_module.unescape(text)
        except:
            pass
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Remove remaining navigation fragments and garbage patterns
        # Remove patterns like "nav" }'>" or "_nav", " or "cN" >"
        text = re.sub(r'nav"\s*[}>]', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'_[Nn]av"', ' ', text)
        text = re.sub(r'cN"\s*>', ' ', text)
        text = re.sub(r'[a-zA-Z]+"\s*[}>]', ' ', text)  # Any word" followed by } or >
        text = re.sub(r'>[^<]*</[a-z]+>', ' ', text)  # HTML tag remnants like ">text</li>"
        
        # Remove words that are clearly garbage (navigation fragments)
        words = text.split()
        cleaned_words = []
        for word in words:
            # Skip words that are mostly underscores, numbers, or look like IDs
            if '_nav' in word.lower() or word.lower().endswith('_nav') or word.lower().startswith('nav'):
                continue
            if re.match(r'^[a-z]\d+[a-z]\d+', word.lower()):  # ID-like pattern
                continue
            if word in [',', '}', '{', '"', "'", "'>", '"}', '"}', '}>']:  # Single punctuation or fragments
                continue
            if word.startswith('>') or word.endswith('<') or word.startswith("'>") or word.endswith('"'):
                continue  # HTML fragments
            if 'js-' in word.lower() or 'class=' in word.lower():  # HTML attribute fragments
                continue
            cleaned_words.append(word)
        
        text = ' '.join(cleaned_words)
        
        # If it's mostly garbage, return empty
        if len(text) > 0:
            alphanumeric_chars = sum(1 for c in text if c.isalnum())
            if alphanumeric_chars / len(text) < 0.5:
                return ''  # Too many special characters
        
        # Remove trailing punctuation/symbols that might be left over
        text = text.strip(' .,;:!?{}"\'')
        
        # Final check: if description is too short or looks like garbage, skip it
        if len(text) < 10:
            return ''  # Too short to be meaningful
        
        return text[:500] if text else ''
    
    def save_events_to_database(self, events: List[Dict[str, Any]]) -> int:
        """Save events to database"""
        saved_count = 0
        for event in events:
            try:
                iso_date = self._parse_date_to_iso(event.get('date', ''), f"{event.get('title','')} {event.get('description','')}")
                if not iso_date:
                    # Skip events without a valid future date
                    continue
                event['date'] = iso_date
                
                # Clean description before saving
                if 'description' in event:
                    event['description'] = self._clean_description(event['description'])

                event_id = self.db.add_computing_event(event)
                if event_id:
                    saved_count += 1
                    print(f"Saved event: {event['title']} (Date: {event['date']}, Source: {event.get('source', 'Unknown')})")
            except Exception as e:
                print(f"Error saving event {event.get('title', 'Unknown')}: {e}")
        
        return saved_count

    def _parse_date_to_iso(self, date_str: str, fallback_text: str) -> Optional[str]:
        """Normalize various date formats to ISO (YYYY-MM-DD) and require future or today.
        Returns ISO date string or None if invalid/past."""
        import re
        from datetime import datetime, date

        def _try_formats(s: str) -> Optional[date]:
            s = s.strip()
            fmts = [
                '%Y-%m-%d',    # 2025-10-31
                '%m/%d/%Y',    # 10/31/2025
                '%d-%m-%Y',    # 31-10-2025
                '%B %d, %Y',   # October 31, 2025
                '%b %d, %Y',   # Oct 31, 2025
                '%B %d %Y',    # October 31 2025
                '%b %d %Y',    # Oct 31 2025
            ]
            for fmt in fmts:
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    pass
            return None

        today = datetime.now().date()

        # 1) If date_str is provided, try parse directly
        if date_str:
            d = _try_formats(date_str)
            if d and d >= today:
                return d.isoformat()

        # 2) Try to extract a date from fallback text (title+description)
        text = fallback_text or ''
        # Try common textual patterns first
        patterns = [
            r'(\d{4}-\d{1,2}-\d{1,2})',  # 2025-10-31
            r'(\d{1,2}/\d{1,2}/\d{4})',  # 10/31/2025
            r'(\d{1,2}-\d{1,2}-\d{4})',  # 10-31-2025
            r'((January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})',
            r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})',
        ]

        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                candidate = m.group(1)
                d = _try_formats(candidate)
                if d and d >= today:
                    return d.isoformat()

        # 3) As a final heuristic, accept phrases like "tomorrow", "next week", etc., as today (but do not backdate)
        lower = text.lower()
        if any(k in lower for k in ['tomorrow', 'next week', 'next month', 'upcoming', 'this week', 'this month']):
            return today.isoformat()

        return None


def main():
    """Main function for command line usage"""
    searcher = EnhancedTechComputingSearcher()
    
    print("🔍 Enhanced tech search for computing events...")
    events = searcher.search_events(max_results=30)
    
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
        categories = {}
        
        for event in events:
            host = event.get('host', 'Other')
            cost_type = event.get('cost_type', 'Unknown')
            source = event.get('source', 'Unknown')
            event_categories = event.get('categories', [])
            
            hosts[host] = hosts.get(host, 0) + 1
            cost_types[cost_type] = cost_types.get(cost_type, 0) + 1
            sources[source] = sources.get(source, 0) + 1
            
            for category in event_categories:
                categories[category] = categories.get(category, 0) + 1
        
        print("\nEvents by Host:")
        for host, count in sorted(hosts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {host}: {count}")
        
        print("\nEvents by Cost Type:")
        for cost_type, count in sorted(cost_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cost_type}: {count}")
        
        print("\nEvents by Source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
        
        print("\nEvents by Category:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
