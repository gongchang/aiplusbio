from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import json
from event_scraper import EventScraper
from event_categorizer import EventCategorizer
from database import Database

app = Flask(__name__)
CORS(app)

# Initialize components
db = Database()
scraper = EventScraper(db)
categorizer = EventCategorizer()

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    """API endpoint to get all events with optional filtering"""
    try:
        # Get filter parameters
        search_query = request.args.get('search', '').lower()
        cs_filter = request.args.get('cs', 'false').lower() == 'true'
        biology_filter = request.args.get('biology', 'false').lower() == 'true'
        
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
    
    # Get event count
    events = db.get_events()
    print(f"📊 Loaded {len(events)} existing events from database")
    
    print("🚀 Starting AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area (No Background Scraping)...")
    print("📊 Web interface will be available at: http://localhost:5001")
    print("⚠️  Background scraping is DISABLED - use 'Refresh Events' button to scrape manually")
    print("⏹️  Press Ctrl+C to stop the application")
    print("-" * 50)
    
    # Run Flask app WITHOUT background scraping
    app.run(debug=True, host='0.0.0.0', port=5001) 