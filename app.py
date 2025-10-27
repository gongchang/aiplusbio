from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import json
from event_scraper import EventScraper
from event_categorizer import EventCategorizer
from database import Database
from computing_event_searcher import ComputingEventSearcher
from enhanced_computing_event_searcher import EnhancedComputingEventSearcher
from improved_tavily_searcher import ImprovedTavilySearcher
from free_api_computing_searcher import FreeAPIComputingSearcher

app = Flask(__name__)
CORS(app)

# Initialize components
db = Database()
scraper = EventScraper(db)
categorizer = EventCategorizer()
computing_searcher = ComputingEventSearcher()
enhanced_computing_searcher = EnhancedComputingEventSearcher()
improved_tavily_searcher = ImprovedTavilySearcher()
free_api_searcher = FreeAPIComputingSearcher()

# Cache for virtual worldwide events descriptions
_virtual_events_cache = {}
_cache_timestamp = None
_cache_duration = 3600  # Cache for 1 hour

# Cache for social media content
_social_media_cache = {}
_social_media_cache_timestamp = None
_social_media_cache_duration = 1800  # Cache for 30 minutes

def scrape_website_description(url):
    """Scrape description from a website URL"""
    description = 'AI + Biology related content'
    try:
        import requests
        from bs4 import BeautifulSoup
        import re

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to extract meaningful description
            # Look for meta description first
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content')
            else:
                # Look for og:description
                og_desc = soup.find('meta', attrs={'property': 'og:description'})
                if og_desc and og_desc.get('content'):
                    description = og_desc.get('content')
                else:
                    # Try to get first paragraph or summary
                    paragraphs = soup.find_all(['p', 'div'], class_=re.compile(r'description|summary|intro|about'))
                    if paragraphs:
                        description = paragraphs[0].get_text().strip()
                    else:
                        # Get first meaningful paragraph
                        paragraphs = soup.find_all('p')
                        for p in paragraphs:
                            text = p.get_text().strip()
                            if len(text) > 50 and len(text) < 300:
                                description = text
                                break

            # Clean up description
            if description:
                description = re.sub(r'\s+', ' ', description)
                description = description[:200] + '...' if len(description) > 200 else description

    except Exception as e:
        # If scraping fails, use default description
        description = 'AI + Biology related content'

    return description

def fetch_youtube_videos(channel_id, max_results=1):
    """Fetch recent videos from YouTube channel using RSS feed"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        
        # Try different RSS feed formats for YouTube
        rss_urls = []
        
        if '@' in channel_id:
            channel_name = channel_id.replace('@', '')
            # Try multiple RSS feed formats for @username
            rss_urls = [
                f"https://www.youtube.com/feeds/videos.xml?user={channel_name}",
                f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_name}",
                f"https://www.youtube.com/feeds/videos.xml?username={channel_name}"
            ]
        else:
            rss_urls = [f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for rss_url in rss_urls:
            try:
                print(f"Trying RSS URL: {rss_url}")
                response = requests.get(rss_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    
                    videos = []
                    entries = soup.find_all('entry')[:max_results]
                    
                    for entry in entries:
                        title_elem = entry.find('title')
                        link_elem = entry.find('link')
                        published_elem = entry.find('published')
                        
                        if title_elem and link_elem:
                            title = title_elem.get_text().strip()
                            link = link_elem.get('href', '')
                            published = published_elem.get_text().strip() if published_elem else ''
                            
                            video_info = {
                                'title': title,
                                'url': link,
                                'published': published,
                                'thumbnail': ''
                            }
                            videos.append(video_info)
                    
                    if videos:
                        print(f"Successfully found {len(videos)} videos from RSS feed")
                        return videos
                        
            except Exception as e:
                print(f"Error with RSS URL {rss_url}: {e}")
                continue
        
        # If RSS feeds fail, try web scraping as fallback
        print("RSS feeds failed, trying web scraping...")
        if '@' in channel_id:
            channel_name = channel_id.replace('@', '')
            channel_url = f"https://www.youtube.com/@{channel_name}"
        else:
            channel_url = f"https://www.youtube.com/channel/{channel_id}"
        
        response = requests.get(channel_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            videos = []
            
            # Look for video titles in the page
            video_elements = soup.find_all(['h3', 'a', 'div'], 
                                         class_=lambda x: x and any(word in x.lower() for word in ['title', 'video', 'ytd']))
            
            for element in video_elements[:max_results * 3]:
                title = element.get_text().strip()
                if (title and len(title) > 10 and len(title) < 100 and 
                    not any(word in title.lower() for word in ['home', 'videos', 'playlists', 'community', 'about', 'search'])):
                    
                    video_url = element.get('href', '')
                    if video_url and '/watch?v=' in video_url:
                        full_url = f"https://www.youtube.com{video_url}" if video_url.startswith('/') else video_url
                    else:
                        full_url = channel_url
                    
                    video_info = {
                        'title': title,
                        'url': full_url,
                        'published': '',
                        'thumbnail': ''
                    }
                    videos.append(video_info)
                    
                    if len(videos) >= max_results:
                        break
            
            return videos
        
        return []
            
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return []

def fetch_spotify_episodes(show_id, max_results=1):
    """Fetch recent episodes from Spotify podcast using web scraping"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try to get show info from Spotify web page
        show_url = f"https://open.spotify.com/show/{show_id}"
        response = requests.get(show_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            episodes = []
            
            # Try to find episode titles in the page content
            # Look for common Spotify episode patterns
            episode_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'div', 'span'], 
                                           class_=lambda x: x and any(word in x.lower() for word in ['episode', 'title', 'track', 'name']))
            
            for element in episode_elements[:max_results * 5]:  # Get more elements to filter
                title = element.get_text().strip()
                # Filter for likely episode titles (not too short, not navigation text)
                if (title and len(title) > 10 and len(title) < 100 and 
                    not any(word in title.lower() for word in ['spotify', 'podcast', 'follow', 'share', 'play', 'pause'])):
                    
                    episode_data = {
                        'title': title,
                        'url': show_url,
                        'published': '',
                        'thumbnail': ''
                    }
                    episodes.append(episode_data)
                    
                    if len(episodes) >= max_results:
                        break
            
            # If no episodes found with the above method, try a simpler approach
            if not episodes:
                # Look for any text that might be an episode title
                all_text_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'span', 'div'])
                for element in all_text_elements:
                    title = element.get_text().strip()
                    if (title and len(title) > 15 and len(title) < 80 and 
                        not any(word in title.lower() for word in ['spotify', 'podcast', 'follow', 'share', 'play', 'pause', 'episode'])):
                        
                        episode_data = {
                            'title': title,
                            'url': show_url,
                            'published': '',
                            'thumbnail': ''
                        }
                        episodes.append(episode_data)
                        
                        if len(episodes) >= max_results:
                            break
            
            return episodes
        else:
            print(f"Failed to fetch Spotify show page: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching Spotify episodes: {e}")
        return []

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/virtual-worldwide')
def virtual_worldwide():
    """Serve the virtual worldwide events page"""
    return render_template('virtual_worldwide.html')

@app.route('/social-media')
def social_media():
    """Serve the social media page"""
    return render_template('social_media.html')

@app.route('/computing-events')
def computing_events():
    """Serve the computing events page"""
    return render_template('computing_events.html')

@app.route('/api/events')
def get_events():
    """API endpoint to get all events with optional filtering"""
    try:
        # Get filter parameters
        search_query = request.args.get('search', '').lower()
        cs_filter = request.args.get('cs', 'false').lower() == 'true'
        biology_filter = request.args.get('biology', 'false').lower() == 'true'
        
        # Get institution filters
        mit_filter = request.args.get('mit', 'true').lower() == 'true'
        harvard_filter = request.args.get('harvard', 'true').lower() == 'true'
        bu_filter = request.args.get('bu', 'true').lower() == 'true'
        brown_filter = request.args.get('brown', 'true').lower() == 'true'
        others_filter = request.args.get('others', 'true').lower() == 'true'
        
        # Get events from database
        events = db.get_events()
        
        # Apply filters
        filtered_events = []
        for event in events:
            # Search filter
            if search_query:
                searchable_text = f"{event.get('title', '')} {event.get('description', '')} {event.get('location', '')}".lower()
                if search_query not in searchable_text:
                    continue
            
            # Category filters
            if cs_filter and 'computer science' not in event.get('categories', []):
                continue
            if biology_filter and 'biology' not in event.get('categories', []):
                continue
            
            # Institution filters
            event_institution = event.get('institution', 'Others')
            if event_institution == 'MIT' and not mit_filter:
                continue
            elif event_institution == 'Harvard' and not harvard_filter:
                continue
            elif event_institution == 'BU' and not bu_filter:
                continue
            elif event_institution == 'Brown' and not brown_filter:
                continue
            elif event_institution == 'Others' and not others_filter:
                continue
                
            filtered_events.append(event)
        
        # Sort by date
        filtered_events.sort(key=lambda x: x.get('date', ''))
        
        return jsonify({
            'success': True,
            'events': filtered_events,
            'total': len(filtered_events)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """API endpoint to manually trigger event scraping"""
    try:
        # Run scraper
        new_events = scraper.scrape_all_sites()
        
        # Categorize new events
        for event in new_events:
            categories = categorizer.categorize_event(event)
            event['categories'] = categories
            db.update_event_categories(event['id'], categories)
        
        return jsonify({
            'success': True,
            'message': f'Successfully scraped {len(new_events)} new events',
            'new_events': len(new_events)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/computing-events')
def get_computing_events():
    """API endpoint to get all computing events with optional filtering"""
    try:
        # Get filter parameters
        search_query = request.args.get('search', '').lower()
        free_filter = request.args.get('free', 'true').lower() == 'true'
        paid_filter = request.args.get('paid', 'true').lower() == 'true'
        unknown_filter = request.args.get('unknown', 'true').lower() == 'true'
        
        # Get host filters
        hosts_param = request.args.get('hosts', '')
        selected_hosts = set(hosts_param.split(',')) if hosts_param else set()
        
        # Get events from database
        events = db.get_computing_events()
        
        # Apply filters
        filtered_events = []
        for event in events:
            # Search filter
            if search_query:
                searchable_text = f"{event.get('title', '')} {event.get('description', '')} {event.get('location', '')}".lower()
                if search_query not in searchable_text:
                    continue
            
            # Cost type filters
            cost_type = event.get('cost_type', 'Unknown')
            if cost_type == 'Free' and not free_filter:
                continue
            if cost_type == 'Paid' and not paid_filter:
                continue
            if cost_type == 'Unknown' and not unknown_filter:
                continue
            
            # Host filters
            if selected_hosts and event.get('host') not in selected_hosts:
                continue
                
            filtered_events.append(event)
        
        # Sort by date
        filtered_events.sort(key=lambda x: x.get('date', ''))
        
        return jsonify({
            'success': True,
            'events': filtered_events,
            'total': len(filtered_events)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/computing-events/search', methods=['POST'])
def search_computing_events():
    """API endpoint to manually trigger computing event search"""
    try:
        # Use free API searcher for better results (RSS feeds + Eventbrite + Tavily)
        events = free_api_searcher.search_events(max_results=20)
        
        # Save events to database
        saved_count = free_api_searcher.save_events_to_database(events)
        
        return jsonify({
            'success': True,
            'message': f'Successfully searched for computing events using enhanced multi-API search',
            'events_found': len(events),
            'events_saved': saved_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/computing-events/stats')
def get_computing_event_stats():
    """API endpoint to get computing event statistics"""
    try:
        stats = db.get_computing_event_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """API endpoint to get scraping statistics"""
    try:
        stats = db.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/virtual-worldwide')
def get_virtual_worldwide():
    """API endpoint to get virtual worldwide events"""
    global _virtual_events_cache, _cache_timestamp

    try:
        # Check if cache is still valid
        import time
        current_time = time.time()

        if (_cache_timestamp is None or
            current_time - _cache_timestamp > _cache_duration or
            not _virtual_events_cache):

            # Cache expired or empty, rebuild it
            _virtual_events_cache = {}
            _cache_timestamp = current_time

            # Read virtual worldwide events from file
            virtual_events = []
            try:
                with open('virtual_worldwide.txt', 'r') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

                for url in urls:
                    # Extract domain for better categorization
                    from urllib.parse import urlparse
                    try:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.lower()
                        path = parsed_url.path.lower()
                    except:
                        domain = ''
                        path = ''

                    # Get description from cache or scrape it
                    if url not in _virtual_events_cache:
                        _virtual_events_cache[url] = scrape_website_description(url)

                    description = _virtual_events_cache[url]

                    # YouTube channels
                    if 'youtube.com' in url or 'youtu.be' in url:
                        # Extract channel name from YouTube URL
                        channel_name = 'AI + Biology YouTube Channel'
                        if '@' in url:
                            channel_name = url.split('@')[1].split('/')[0]
                        elif 'channel/' in url:
                            # For channel IDs, we'll use a more descriptive name
                            channel_id = url.split('channel/')[1].split('/')[0]
                            # Try to get a more meaningful name based on the channel ID
                            if channel_id == 'UCiiOj5GSES6uw21kfXnxj3A':
                                channel_name = 'Online Causal Inference Seminar'
                            else:
                                channel_name = f'AI + Biology Channel ({channel_id[:8]}...)'
                        elif 'user/' in url:
                            channel_name = url.split('user/')[1].split('/')[0]
                        elif 'c/' in url:
                            channel_name = url.split('c/')[1].split('/')[0]

                        virtual_events.append({
                            'type': 'youtube',
                            'url': url,
                            'title': f'YouTube: {channel_name}',
                            'description': description
                        })

                    # Known specific sites (prioritized before general categories)
                    elif 'genbio.ai' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'GenBio AI Seminar Series',
                            'description': description
                        })
                    elif 'snap.stanford.edu' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'Stanford AI-Bio Seminar',
                            'description': description
                        })
                    elif 'statsupai.org' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'StatsUP-AI Health Data Science',
                            'description': description
                        })
                    elif 'bpdmc.org' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'BPDMC Seminar Series',
                            'description': description
                        })
                    elif 'ai.ucsf.edu' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'UCSF AI Seminar Series',
                            'description': description
                        })

                    # Seminar series (general)
                    elif any(keyword in domain for keyword in ['seminar', 'talk', 'lecture', 'workshop']):
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': f'Seminar Series - {domain}',
                            'description': description
                        })

                    # Conference websites (general)
                    elif any(keyword in domain for keyword in ['conference', 'symposium', 'meeting', 'congress']):
                        virtual_events.append({
                            'type': 'conference',
                            'url': url,
                            'title': f'Conference - {domain}',
                            'description': description
                        })

                    # Research institutions (general)
                    elif any(keyword in domain for keyword in ['edu', 'university', 'institute', 'lab', 'research']):
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': f'Research Event - {domain}',
                            'description': description
                        })

                    # Default for unknown sites
                    else:
                        virtual_events.append({
                            'type': 'other',
                            'url': url,
                            'title': f'Virtual Event - {domain}',
                            'description': description
                        })
            except FileNotFoundError:
                virtual_events = []
        else:
            # Cache is still valid, use cached data
            virtual_events = []
            try:
                with open('virtual_worldwide.txt', 'r') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

                for url in urls:
                    # Extract domain for better categorization
                    from urllib.parse import urlparse
                    try:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.lower()
                        path = parsed_url.path.lower()
                    except:
                        domain = ''
                        path = ''

                    # Get description from cache
                    description = _virtual_events_cache.get(url, 'AI + Biology related content')

                    # YouTube channels
                    if 'youtube.com' in url or 'youtu.be' in url:
                        # Extract channel name from YouTube URL
                        channel_name = 'AI + Biology YouTube Channel'
                        if '@' in url:
                            channel_name = url.split('@')[1].split('/')[0]
                        elif 'channel/' in url:
                            # For channel IDs, we'll use a more descriptive name
                            channel_id = url.split('channel/')[1].split('/')[0]
                            # Try to get a more meaningful name based on the channel ID
                            if channel_id == 'UCiiOj5GSES6uw21kfXnxj3A':
                                channel_name = 'Online Causal Inference Seminar'
                            else:
                                channel_name = f'AI + Biology Channel ({channel_id[:8]}...)'
                        elif 'user/' in url:
                            channel_name = url.split('user/')[1].split('/')[0]
                        elif 'c/' in url:
                            channel_name = url.split('c/')[1].split('/')[0]

                        virtual_events.append({
                            'type': 'youtube',
                            'url': url,
                            'title': f'YouTube: {channel_name}',
                            'description': description
                        })

                    # Known specific sites (prioritized before general categories)
                    elif 'genbio.ai' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'GenBio AI Seminar Series',
                            'description': description
                        })
                    elif 'snap.stanford.edu' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'Stanford AI-Bio Seminar',
                            'description': description
                        })
                    elif 'statsupai.org' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'StatsUP-AI Health Data Science',
                            'description': description
                        })
                    elif 'bpdmc.org' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'BPDMC Seminar Series',
                            'description': description
                        })
                    elif 'ai.ucsf.edu' in url:
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': 'UCSF AI Seminar Series',
                            'description': description
                        })

                    # Seminar series (general)
                    elif any(keyword in domain for keyword in ['seminar', 'talk', 'lecture', 'workshop']):
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': f'Seminar Series - {domain}',
                            'description': description
                        })

                    # Conference websites (general)
                    elif any(keyword in domain for keyword in ['conference', 'symposium', 'meeting', 'congress']):
                        virtual_events.append({
                            'type': 'conference',
                            'url': url,
                            'title': f'Conference - {domain}',
                            'description': description
                        })

                    # Research institutions (general)
                    elif any(keyword in domain for keyword in ['edu', 'university', 'institute', 'lab', 'research']):
                        virtual_events.append({
                            'type': 'seminar',
                            'url': url,
                            'title': f'Research Event - {domain}',
                            'description': description
                        })

                    # Default for unknown sites
                    else:
                        virtual_events.append({
                            'type': 'other',
                            'url': url,
                            'title': f'Virtual Event - {domain}',
                            'description': description
                        })
            except FileNotFoundError:
                virtual_events = []

        return jsonify({
            'success': True,
            'events': virtual_events
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/social-media')
def get_social_media():
    """API endpoint to get social media channels with dynamic content"""
    global _social_media_cache, _social_media_cache_timestamp
    
    try:
        # Check if cache is still valid
        import time
        current_time = time.time()
        
        if (_social_media_cache_timestamp is None or 
            current_time - _social_media_cache_timestamp > _social_media_cache_duration or 
            not _social_media_cache):
            
            # Cache expired or empty, rebuild it
            _social_media_cache = {}
            _social_media_cache_timestamp = current_time
            
            # Read social media channels from file
            social_channels = []
            try:
                with open('social_media.txt', 'r') as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                for url in urls:
                    # Extract domain for better categorization
                    from urllib.parse import urlparse
                    try:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.lower()
                    except:
                        domain = ''
                    
                    # YouTube channels
                    if 'youtube.com' in url or 'youtu.be' in url:
                        # Extract channel name
                        channel_name = 'AI + Bio'
                        channel_id = None
                        if '@' in url:
                            channel_name = url.split('@')[1].split('/')[0]
                            channel_id = url.split('@')[1].split('/')[0]
                        elif 'channel/' in url:
                            # For channel IDs, we'll use a more descriptive name
                            channel_id = url.split('channel/')[1].split('/')[0]
                            channel_name = f'Channel {channel_id[:8]}...'
                        elif 'user/' in url:
                            channel_name = url.split('user/')[1].split('/')[0]
                            channel_id = url.split('user/')[1].split('/')[0]
                        elif 'c/' in url:
                            channel_name = url.split('c/')[1].split('/')[0]
                            channel_id = url.split('c/')[1].split('/')[0]
                        
                        # Fetch recent videos
                        recent_videos = []
                        if channel_id:
                            print(f"Fetching videos for channel: {channel_id}")
                            recent_videos = fetch_youtube_videos(channel_id, max_results=1)
                            print(f"Found {len(recent_videos)} videos for {channel_id}")
                            
                            # If no videos found, provide meaningful sample content
                            if not recent_videos:
                                print(f"No videos found for {channel_id}, using sample content")
                                recent_videos = [
                                    {
                                        'title': 'Latest AI + Biology Content (Sample)',
                                        'url': f"https://www.youtube.com/@{channel_id.replace('@', '')}",
                                        'published': 'Recent',
                                        'thumbnail': ''
                                    }
                                ]
                        
                        social_channels.append({
                            'platform': 'youtube',
                            'url': url,
                            'title': f'AI + Bio YouTube: {channel_name}',
                            'description': 'Latest videos and content about AI and Biology',
                            'channel_id': channel_id,
                            'recent_content': recent_videos
                        })
                    
                    # Spotify podcasts
                    elif 'spotify.com' in url:
                        show_name = 'AI + Bio Podcast'
                        show_id = None
                        if 'show/' in url:
                            show_id = url.split('show/')[1].split('?')[0]
                        
                        # Fetch recent episodes
                        recent_episodes = []
                        if show_id:
                            print(f"Fetching episodes for show: {show_id}")
                            recent_episodes = fetch_spotify_episodes(show_id, max_results=1)
                            print(f"Found {len(recent_episodes)} episodes for {show_id}")
                            
                            # If no episodes found or if content is blocked, provide meaningful sample content
                            if not recent_episodes or (recent_episodes and 'Unsupported browser' in recent_episodes[0].get('title', '')):
                                print(f"No episodes found for {show_id}, using sample content")
                                recent_episodes = [
                                    {
                                        'title': 'Latest AI + Biology Podcast Episode (Sample)',
                                        'url': url,
                                        'published': 'Recent',
                                        'thumbnail': ''
                                    }
                                ]
                        
                        social_channels.append({
                            'platform': 'spotify',
                            'url': url,
                            'title': show_name,
                            'description': 'Latest episodes and discussions about AI and Biology',
                            'show_id': show_id,
                            'recent_content': recent_episodes
                        })
                    
                    # Apple Podcasts
                    elif 'podcasts.apple.com' in url:
                        social_channels.append({
                            'platform': 'apple_podcasts',
                            'url': url,
                            'title': 'AI + Bio Apple Podcast',
                            'description': 'Latest episodes on Apple Podcasts',
                            'podcast_id': url.split('id')[1].split('?')[0] if 'id' in url else None,
                            'recent_content': []
                        })
                    
                    # Twitter/X
                    elif 'twitter.com' in url or 'x.com' in url:
                        handle = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
                        social_channels.append({
                            'platform': 'twitter',
                            'url': url,
                            'title': f'AI + Bio Twitter: @{handle}',
                            'description': 'Latest updates and discussions on Twitter/X',
                            'handle': handle,
                            'recent_content': []
                        })
                    
                    # LinkedIn
                    elif 'linkedin.com' in url:
                        social_channels.append({
                            'platform': 'linkedin',
                            'url': url,
                            'title': 'AI + Bio LinkedIn',
                            'description': 'Professional network and updates',
                            'profile_id': url.split('/')[-1] if url.endswith('/') else url.split('/')[-1],
                            'recent_content': []
                        })
                    
                    # Default for unknown platforms
                    else:
                        social_channels.append({
                            'platform': 'other',
                            'url': url,
                            'title': f'AI + Bio - {domain}',
                            'description': 'Social media content about AI and Biology',
                            'platform_name': domain,
                            'recent_content': []
                        })
                
                # Store in cache
                _social_media_cache = social_channels
                
            except FileNotFoundError:
                social_channels = []
        else:
            # Cache is still valid, use cached data
            social_channels = _social_media_cache
        
        return jsonify({
            'success': True,
            'channels': social_channels
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/calendar.ics')
def generate_ical():
    """Generate iCal feed for all events"""
    try:
        events = db.get_events()
        
        # Generate iCal content
        ical_content = generate_ical_content(events)
        
        response = Response(ical_content, mimetype='text/calendar')
        response.headers['Content-Disposition'] = 'attachment; filename=aiplusbio_events.ics'
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/calendar/<filter_type>')
def generate_filtered_ical(filter_type):
    """Generate iCal feed for filtered events"""
    try:
        events = db.get_events()
        filtered_events = []
        
        if filter_type == 'cs':
            filtered_events = [e for e in events if 'computer science' in e.get('categories', [])]
        elif filter_type == 'biology':
            filtered_events = [e for e in events if 'biology' in e.get('categories', [])]
        elif filter_type == 'all':
            filtered_events = events
        else:
            return jsonify({'error': 'Invalid filter type'}), 400
        
        # Generate iCal content
        ical_content = generate_ical_content(filtered_events)
        
        response = Response(ical_content, mimetype='text/calendar')
        response.headers['Content-Disposition'] = f'attachment; filename=aiplusbio_{filter_type}_events.ics'
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_ical_content(events):
    """Generate iCal content from events"""
    ical_lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:AI+Bio Events',
        'X-WR-CALDESC:Academic events from MIT and Harvard',
    ]
    
    for event in events:
        # Parse event date and time
        event_date = event.get('date', '')
        event_time = event.get('time', '')
        
        if not event_date:
            continue
            
        # Create start and end times
        start_dt = datetime.strptime(event_date, '%Y-%m-%d')
        if event_time:
            # Try to parse time (this is simplified - you might want more robust time parsing)
            try:
                time_parts = event_time.replace('AM', ' AM').replace('PM', ' PM').split(':')
                if len(time_parts) >= 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1].split()[0])
                    if 'PM' in event_time and hour != 12:
                        hour += 12
                    if 'AM' in event_time and hour == 12:
                        hour = 0
                    start_dt = start_dt.replace(hour=hour, minute=minute)
            except:
                pass
        
        # End time is 1 hour after start (default)
        end_dt = start_dt + timedelta(hours=1)
        
        # Format dates for iCal
        start_str = start_dt.strftime('%Y%m%dT%H%M%S')
        end_str = end_dt.strftime('%Y%m%dT%H%M%S')
        
        # Create unique ID
        event_id = f"aiplusbio_{event.get('id', 'unknown')}_{start_str}"
        
        # Escape text for iCal
        title = event.get('title', '').replace('\n', '\\n').replace('\r', '\\r')
        description = event.get('description', '').replace('\n', '\\n').replace('\r', '\\r')
        location = event.get('location', '').replace('\n', '\\n').replace('\r', '\\r')
        url = event.get('url', '')
        
        # Build event
        event_lines = [
            'BEGIN:VEVENT',
            f'UID:{event_id}',
            f'DTSTART:{start_str}',
            f'DTEND:{end_str}',
            f'SUMMARY:{title}',
        ]
        
        if description:
            event_lines.append(f'DESCRIPTION:{description}')
        if location:
            event_lines.append(f'LOCATION:{location}')
        if url:
            event_lines.append(f'URL:{url}')
        
        event_lines.extend([
            'STATUS:CONFIRMED',
            'SEQUENCE:0',
            'END:VEVENT'
        ])
        
        ical_lines.extend(event_lines)
    
    ical_lines.append('END:VCALENDAR')
    return '\r\n'.join(ical_lines)

if __name__ == '__main__':
    # Initialize database
    db.init_db()
    
    # Start background scraper (currently enabled - runs every 6 hours)
    scraper.start_background_scraping()
    
    # Get port from environment variable (required for Cloud Run)
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Run Flask app
    app.run(debug=debug, host='0.0.0.0', port=port) 