from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import os
import hmac
import tempfile
from pathlib import Path
from datetime import timezone
from datetime import datetime, timedelta
import json
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from urllib.parse import urlparse
from event_scraper import EventScraper
from event_dedupe import unique_events
from computing_scraper import scrape_free_events, ALLOWED_SOURCES
from event_categorizer import EventCategorizer
from database import Database

SERVERLESS = bool(os.getenv('VERCEL'))
if SERVERLESS:
    os.environ['DATABASE_PATH'] = '/tmp/aiplusbio-web.db'
USE_FIRESTORE = SERVERLESS or os.getenv('USE_FIRESTORE', 'false').lower() == 'true'
if USE_FIRESTORE:
    from firestoreservice import EventStore
    event_store = EventStore()
    computing_store = EventStore('computing_events')
else:
    event_store = None
    computing_store = None

app = Flask(__name__, static_folder='public/static')
CORS(app)
app.jinja_env.globals['serverless'] = SERVERLESS

# Initialize components
db = Database()
scraper = EventScraper(db)
categorizer = EventCategorizer()

DEFAULT_DESCRIPTION = 'AI + Biology related content'
PRIMARY_INSTITUTIONS = ('MIT', 'Harvard', 'BU', 'Brown')

# Cache for virtual worldwide event cards and descriptions
_virtual_events_cache = []
_virtual_description_cache = {}
_virtual_cache_signature = None
_virtual_cache_lock = Lock()
_cache_timestamp = None
_cache_duration = 3600  # Cache for 1 hour

# Cache for social media content
_social_media_cache = {}
_social_media_cache_timestamp = None
_social_media_cache_duration = 1800  # Cache for 30 minutes

def _prepare_events_for_firestore(events):
    normalised = []
    for event in events:
        data = dict(event)
        source_url = data.get('source_url') or data.get('url') or ''
        data['source_url'] = source_url
        data['url'] = data.get('url') or source_url
        data['institution'] = data.get('institution') or db.get_institution_from_url(source_url)
        data['is_virtual'] = bool(data.get('is_virtual', False))
        data['requires_registration'] = bool(data.get('requires_registration', False))
        if 'categories' not in data or data['categories'] is None:
            data['categories'] = []
        normalised.append(data)
    return normalised


def _bool_query_arg(name, default=True):
    default_value = 'true' if default else 'false'
    return request.args.get(name, default_value).lower() == 'true'


def _selected_institution_filters():
    selected = []
    if _bool_query_arg('mit'):
        selected.append('MIT')
    if _bool_query_arg('harvard'):
        selected.append('Harvard')
    if _bool_query_arg('bu'):
        selected.append('BU')
    if _bool_query_arg('brown'):
        selected.append('Brown')
    return selected, _bool_query_arg('others')


def _event_matches_institution_filters(event, selected_institutions, include_other_institutions):
    institution = event.get('institution') or 'Others'
    if institution in PRIMARY_INSTITUTIONS:
        return institution in selected_institutions
    return include_other_institutions


def _read_url_list(filename):
    try:
        with open(filename, 'r') as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.lstrip().startswith('#')
            ]
    except FileNotFoundError:
        return []


def scrape_website_description(url):
    """Scrape description from a website URL"""
    description = DEFAULT_DESCRIPTION
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
        description = DEFAULT_DESCRIPTION

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
        search_query = request.args.get('search', '').strip().lower()
        selected_institutions, include_other_institutions = _selected_institution_filters()
        
        if USE_FIRESTORE and event_store:
            events = event_store.list_events(limit=500)
            filtered_events = []
            for event in events:
                if search_query:
                    searchable_text = f"{event.get('title', '')} {event.get('description', '')} {event.get('location', '')}".lower()
                    if search_query not in searchable_text:
                        continue
                if not _event_matches_institution_filters(
                    event,
                    selected_institutions,
                    include_other_institutions
                ):
                    continue
                filtered_events.append(event)
            filtered_events.sort(key=lambda x: (x.get('date', ''), x.get('time', '')))
        else:
            filtered_events = db.get_events(
                search_query=search_query or None,
                institutions=selected_institutions,
                include_other_institutions=include_other_institutions
            )
        filtered_events = unique_events(filtered_events)

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
    """Local-only manual scraper; production runs through authenticated cron."""
    if SERVERLESS:
        return jsonify({'success': False, 'error': 'Use the daily scheduled refresh.'}), 403
    try:
        # Run scraper
        new_events = scraper.scrape_all_sites()
        
        # Categorize new events
        for event in new_events:
            categories = categorizer.categorize_event(event)
            event['categories'] = categories
            db.update_event_categories(event['id'], categories)

        if USE_FIRESTORE and event_store and new_events:
            event_store.upsert_events(_prepare_events_for_firestore(new_events))
        
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

@app.route('/api/cron/scrape')
def scheduled_scrape():
    secret = os.getenv('CRON_SECRET')
    if not secret:
        return jsonify({'error': 'CRON_SECRET is not configured'}), 503
    if not hmac.compare_digest(request.headers.get('Authorization', ''), f'Bearer {secret}'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not USE_FIRESTORE:
        return jsonify({'error': 'Firestore is required for scheduled scraping'}), 503

    # ponytail: five sites/day keeps the invocation bounded; increase only after measuring duration.
    with tempfile.TemporaryDirectory() as directory:
        scrape_db = Database(str(Path(directory) / 'events.db'))
        worker = EventScraper(scrape_db)
        worker.serverless = True
        sites = worker.websites
        offset = (datetime.now(timezone.utc).date().toordinal() * 5) % len(sites) if sites else 0
        selected = (sites + sites)[offset:offset + min(5, len(sites))]
        count, errors = 0, []
        for site in selected:
            try:
                events = worker.scrape_website(site)
                for event in events:
                    event['categories'] = categorizer.categorize_event(event)
                count += event_store.upsert_events(_prepare_events_for_firestore(events))
            except Exception as exc:
                app.logger.exception('Failed scraping %s', site)
                errors.append({'site': site, 'error': str(exc)})
    try:
        computing_count = _refresh_computing_events()
    except Exception as exc:
        app.logger.exception('Failed refreshing computing events')
        computing_count = 0
        errors.append({'site': 'computing', 'error': str(exc)})
    return jsonify({'sites': len(selected), 'events': count, 'computing_events': computing_count, 'errors': errors}), 502 if errors else 200


def _refresh_computing_events():
    events = scrape_free_events()
    if USE_FIRESTORE:
        return computing_store.upsert_events(events)
    for event in events:
        db.add_computing_event(event)
    return len(events)


@app.route('/api/computing-events')
def get_computing_events():
    """API endpoint to get all computing events with optional filtering"""
    try:
        search_query = request.args.get('search', '').strip().lower()
        hosts_param = request.args.get('hosts', '')
        selected_hosts = [host for host in hosts_param.split(',') if host] if hosts_param else None
        events = (computing_store.list_events(limit=500) if USE_FIRESTORE else
                  db.get_computing_events(cost_types=['Free']))
        filtered_events = [e for e in events if e.get('cost_type') == 'Free' and e.get('source') in ALLOWED_SOURCES
                           and (not search_query or search_query in
                                f"{e.get('title', '')} {e.get('description', '')} {e.get('location', '')}".lower())
                           and (not selected_hosts or e.get('host') in selected_hosts)]
        
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
    if SERVERLESS:
        return jsonify({'success': False, 'error': 'Events refresh daily; manual refresh is local only.'}), 403
    try:
        saved_count = _refresh_computing_events()
        
        return jsonify({
            'success': True,
            'message': 'Refreshed verified free computing events',
            'events_found': saved_count,
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
        events = (computing_store.list_events(limit=500) if USE_FIRESTORE else db.get_computing_events(cost_types=['Free']))
        events = [e for e in events if e.get('cost_type') == 'Free' and e.get('source') in ALLOWED_SOURCES]
        today = datetime.now(timezone.utc).date().isoformat()
        week = (datetime.now(timezone.utc).date() + timedelta(days=7)).isoformat()
        stats = {'total_events': len(events), 'today_events': sum(e['date'] == today for e in events),
                 'week_events': sum(today <= e['date'] <= week for e in events),
                 'cost_type_stats': {'Free': len(events)},
                 'host_stats': {h: sum(e.get('host') == h for e in events) for h in {e.get('host') for e in events}},
                 'source_stats': {s: sum(e.get('source') == s for e in events) for s in {e.get('source') for e in events}}}
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
        if USE_FIRESTORE:
            events = event_store.list_events(limit=500)
            today = datetime.utcnow().date()
            stats = {
                'total_events': len(events),
                'today_events': sum(e.get('date') == today.isoformat() for e in events),
                'week_events': sum(today.isoformat() <= e.get('date', '') <= (today + timedelta(days=7)).isoformat() for e in events),
                'recent_scrapes': [],
            }
        else:
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


def _youtube_channel_name(url):
    channel_name = 'AI + Biology YouTube Channel'
    if '@' in url:
        channel_name = url.split('@', 1)[1].split('/')[0]
    elif 'channel/' in url:
        channel_id = url.split('channel/', 1)[1].split('/')[0]
        if channel_id == 'UCiiOj5GSES6uw21kfXnxj3A':
            channel_name = 'Online Causal Inference Seminar'
        else:
            channel_name = f'AI + Biology Channel ({channel_id[:8]}...)'
    elif 'user/' in url:
        channel_name = url.split('user/', 1)[1].split('/')[0]
    elif 'c/' in url:
        channel_name = url.split('c/', 1)[1].split('/')[0]
    return channel_name


def _build_virtual_event(url, description):
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        domain = ''

    if 'youtube.com' in url or 'youtu.be' in url:
        return {
            'type': 'youtube',
            'url': url,
            'title': f'YouTube: {_youtube_channel_name(url)}',
            'description': description
        }

    known_titles = {
        'genbio.ai': 'GenBio AI Seminar Series',
        'snap.stanford.edu': 'Stanford AI-Bio Seminar',
        'statsupai.org': 'StatsUP-AI Health Data Science',
        'bpdmc.org': 'BPDMC Seminar Series',
        'ai.ucsf.edu': 'UCSF AI Seminar Series'
    }
    for domain_key, title in known_titles.items():
        if domain_key in url:
            return {
                'type': 'seminar',
                'url': url,
                'title': title,
                'description': description
            }

    if any(keyword in domain for keyword in ['seminar', 'talk', 'lecture', 'workshop']):
        title = f'Seminar Series - {domain}'
    elif any(keyword in domain for keyword in ['conference', 'symposium', 'meeting', 'congress']):
        title = f'Virtual Seminar Hub - {domain}'
    elif any(keyword in domain for keyword in ['edu', 'university', 'institute', 'lab', 'research']):
        title = f'Research Event - {domain}'
    else:
        title = f'Virtual Seminar - {domain or url}'

    return {
        'type': 'seminar',
        'url': url,
        'title': title,
        'description': description
    }


def _refresh_virtual_description_cache(urls):
    url_set = set(urls)
    for cached_url in list(_virtual_description_cache):
        if cached_url not in url_set:
            _virtual_description_cache.pop(cached_url, None)

    missing_urls = [url for url in urls if url not in _virtual_description_cache]
    if not missing_urls:
        return

    max_workers = min(8, len(missing_urls))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for url, description in zip(missing_urls, executor.map(scrape_website_description, missing_urls)):
            _virtual_description_cache[url] = description or DEFAULT_DESCRIPTION


def _load_virtual_events():
    global _virtual_events_cache, _virtual_cache_signature, _cache_timestamp

    current_time = time.time()
    urls = _read_url_list('virtual_worldwide.txt')
    cache_signature = tuple(urls)
    with _virtual_cache_lock:
        cache_expired = _cache_timestamp is None or current_time - _cache_timestamp > _cache_duration
        if cache_expired or cache_signature != _virtual_cache_signature or not _virtual_events_cache:
            _refresh_virtual_description_cache(urls)
            _virtual_events_cache = [
                _build_virtual_event(url, _virtual_description_cache.get(url, DEFAULT_DESCRIPTION))
                for url in urls
            ]
            _virtual_cache_signature = cache_signature
            _cache_timestamp = current_time

        return list(_virtual_events_cache)


@app.route('/api/virtual-worldwide')
def get_virtual_worldwide():
    """API endpoint to get virtual worldwide events"""
    try:
        return jsonify({
            'success': True,
            'events': _load_virtual_events()
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
        events = unique_events(event_store.list_events(limit=500) if USE_FIRESTORE else db.get_events())
        
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
        events = unique_events(event_store.list_events(limit=500) if USE_FIRESTORE else db.get_events())
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
    if not SERVERLESS:
        scraper.start_background_scraping()
    
    # Get port from environment variable (required for Cloud Run)
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Run Flask app
    app.run(debug=debug, host='0.0.0.0', port=port) 
