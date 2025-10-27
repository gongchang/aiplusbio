# Computing Events Feature

This document describes the new "Other Computing Events Around Boston" feature that has been added to the AI + Biology Seminars website.

## Overview

The computing events feature searches for computing-related events in the Greater Boston area using the Tavily API. It filters events based on five strict criteria that ALL must be met:

1. **Computing-related**: AI, AI agents, Machine learning, computational biology, bioinformatics, cloud computing, devops
2. **Formal events only**: workshop, tutorials, community day, dev days, events, symposium, meeting, conference, webinar, user group
   - **EXCLUDES**: meetups, networking events, happy hours, social events
3. **Local to Greater Boston area, Massachusetts, USA**: Boston, Cambridge, MIT, Harvard, Massachusetts, etc.
4. **Not overlapping with existing tracked websites**: Excludes URLs from `websites_to_watch.txt`
5. **Future events only**: STRICT validation for events held today and beyond (excludes past events)

The system searches for the **top 20 events** that meet all these criteria.

## Features

### Web Interface
- **URL**: `/computing-events`
- **Filters**: 
  - Cost type (Free/Paid/Unknown)
  - Host organizations (Amazon, Google, Microsoft, etc.)
  - Search by title/description/location
- **Event display**: Shows event details, host, cost type, date/time, location
- **Calendar view**: Visual calendar representation (simplified implementation)

### API Endpoints
- `GET /api/computing-events` - Retrieve computing events with filtering
- `POST /api/computing-events/search` - Manually trigger event search
- `GET /api/computing-events/stats` - Get statistics about computing events

### Command Line Tools
- `search_computing_events.py` - Manual search with options
- `daily_computing_search.py` - Automated daily search (for cron jobs)

## Usage

### Manual Search via Command Line
```bash
# Basic search
python search_computing_events.py

# Search with custom options
python search_computing_events.py --max-results 50 --verbose

# Dry run (search but don't save to database)
python search_computing_events.py --dry-run
```

### Manual Search via Web Interface
1. Navigate to `/computing-events`
2. Click "Search Events" button
3. Wait for search to complete
4. View results in the events list

### Automated Daily Search
Set up a cron job to run the daily search script:
```bash
# Add to crontab (runs at 11 PM daily)
0 23 * * * cd /path/to/project && python daily_computing_search.py
```

## Database Schema

The computing events are stored in a separate `computing_events` table with the following fields:
- `id` - Primary key
- `title` - Event title
- `description` - Event description
- `date` - Event date
- `time` - Event time
- `location` - Event location
- `url` - Event URL
- `source_url` - Source URL where event was found
- `is_virtual` - Boolean for virtual events
- `requires_registration` - Boolean for registration requirement
- `categories` - JSON array of event categories
- `host` - Host organization (Amazon, Google, etc.)
- `cost_type` - Free/Paid/Unknown
- `created_at` - Record creation timestamp
- `updated_at` - Record update timestamp

## Configuration

### Environment Variables
- `TAVILY_API` - Tavily API key (required)

### Exclusion URLs
The system automatically excludes URLs from `websites_to_watch.txt` to avoid overlap with existing tracked events.

## Search Criteria

### Computing Keywords (Exact List)
- AI
- AI agents
- Machine learning
- Computational biology
- Bioinformatics
- Cloud computing
- DevOps

### Event Keywords (Exact List - Formal Events Only)
- Workshop
- Tutorials
- Community day
- Dev days
- Events
- Symposium
- Meeting
- Conference
- Webinar
- User group

### Excluded Event Types (Informal Events)
- Meetup/Meetups
- Networking
- Happy hour
- Social events

### Location Keywords (Greater Boston Area, Massachusetts, USA)
- Boston
- Cambridge
- Somerville
- Brookline
- Newton
- Watertown
- Waltham
- Lexington
- Arlington
- Medford
- Massachusetts
- MA
- Greater Boston
- Boston area
- MIT
- Harvard
- Boston University
- BU
- Northeastern

### Future Date Keywords (STRICT Validation)
- Upcoming
- Future
- Next
- Tomorrow
- This week
- This month
- Current year (2025), next year (2026), etc.
- Today
- Tonight
- Specific future dates (e.g., "January 15", "Feb 20")
- "This week", "next week", "this month", "next month"

**Note**: The system now performs strict validation to ensure events are truly future events and excludes past events that may have been incorrectly classified.

## Host Detection

The system automatically detects and categorizes events by host organization based on:
- Domain names (amazon.com → Amazon)
- Content analysis
- Known organization mappings

## Cost Type Detection

Events are categorized as:
- **Free**: Contains keywords like "free", "no cost", "complimentary"
- **Paid**: Contains keywords like "cost", "price", "fee", "ticket", "$"
- **Unknown**: No clear cost indicators

## Files Added/Modified

### New Files
- `computing_event_searcher.py` - Main search functionality
- `search_computing_events.py` - Command line interface
- `daily_computing_search.py` - Automated daily search
- `templates/computing_events.html` - Web interface template
- `COMPUTING_EVENTS_README.md` - This documentation

### Modified Files
- `app.py` - Added routes and API endpoints
- `database.py` - Added computing events table and methods
- `templates/index.html` - Added navigation link
- `requirements.txt` - Updated dependencies

## Troubleshooting

### Common Issues
1. **API Key Error**: Ensure `TAVILY_API` is set in `.env` file
2. **Query Too Long**: Search query is automatically shortened to meet API limits
3. **No Results**: Try adjusting search criteria or check API key validity
4. **Database Errors**: Ensure database is initialized with `db.init_db()`

### Logs
- Manual search: Console output
- Daily search: `computing_events_search.log` file
- Web interface: Browser console and server logs

## Future Enhancements

Potential improvements for the future:
1. More sophisticated date/time parsing
2. Enhanced calendar view with full calendar library
3. Email notifications for new events
4. Event recommendation system
5. Integration with event registration systems
6. Advanced filtering options
7. Event similarity detection
8. Automated event categorization improvements
