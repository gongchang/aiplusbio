# Corporate Events Scraping Feature

## Overview

Added capability to scrape events from URLs listed in `Corporate_events.txt` as an additional source, categorized as "Customized". The system also filters out blog posts that are lists of events (e.g., "top 10 conferences") to ensure only actual events are included.

---

## Implementation

### 1. File Loading (`_load_corporate_event_urls`)
- Reads URLs from `Corporate_events.txt`
- Filters out empty lines and comments (lines starting with `#`)
- Only includes URLs starting with `http`

**File Format**:
```
https://gdg.community.dev/gdg-cloud-boston/
https://www.aicamp.ai/event/events
https://developer.nvidia.com/community
https://www.microsoft.com/en/events/search-catalog/?filters=...
```

### 2. Event Scraping (`_search_corporate_events`)
- Scrapes each URL from `Corporate_events.txt`
- Extracts events using multiple methods:
  - **HTML Link Extraction**: Finds links containing "event", "workshop", "webinar", "conference"
  - **JSON-LD Structured Data**: Extracts events from schema.org Event markup
- Filters out blog posts/lists before processing
- Sets source as `"Customized"`

### 3. Blog Post Filtering (`_is_blog_post_list`)
Filters out blog posts and list articles using multiple indicators:

#### Title Patterns:
- `top \d+` (e.g., "top 10", "top 5")
- `\d+ best` (e.g., "10 best conferences")
- `\d+ must.*attend`
- `list of`
- `guide to`
- `how to (find|choose|pick)`
- `ultimate (guide|list)`
- `complete (guide|list)`
- `roundup of`
- `compilation of`

#### Description Patterns:
- Numbered lists with 3+ items (e.g., "1. Event", "2. Event", "3. Event")
- Hash-numbered items (#1, #2, etc.)

#### URL Patterns:
- `/blog/`
- `/article/`
- `/news/`
- `/posts/`
- `/editorial/`

**Examples of Filtered Out**:
- ❌ "Top 10 AI Conferences in 2026"
- ❌ "5 Best Conferences You Must Attend"
- ❌ "Ultimate Guide to Tech Events"
- ✅ "NVIDIA GTC 2026" (actual event)
- ✅ "Workshop: Machine Learning Fundamentals" (actual event)

### 4. Event Extraction Methods

#### Method 1: HTML Link Extraction
- Searches for links containing event-related keywords
- Extracts title from link text
- Extracts date from surrounding HTML context
- Normalizes relative URLs to absolute URLs

#### Method 2: JSON-LD Structured Data
- Parses `<script type="application/ld+json">` tags
- Extracts events with `@type: "Event"` or `"TechEvent"`
- Uses structured data for accurate date, location, and details

### 5. Integration into Search Flow
```python
# In search_events():
# 1. RSS feeds
# 2. Eventbrite
# 3. Tavily
# 4. Meetup groups
# 5. Corporate events (NEW) ← Added here
```

---

## Event Structure

Events scraped from corporate URLs have the following structure:
```python
{
    'title': 'Event Title',
    'description': 'Event description...',
    'url': 'https://...',  # Individual event URL
    'source_url': 'https://...',  # Original corporate URL
    'is_virtual': True/False,
    'requires_registration': True/False,
    'categories': ['AI/ML', 'Cloud/DevOps', ...],
    'host': 'Google' | 'Microsoft' | 'NVIDIA' | ...,
    'cost_type': 'Free' | 'Paid' | 'Unknown',
    'date': '2026-01-15',
    'time': '14:00',
    'location': 'Boston' | 'Virtual' | ...,
    'source': 'Customized'  # ← Categorized as Customized
}
```

---

## Host Detection

The system automatically detects host organizations from URLs:
- `nvidia.com` → `NVIDIA`
- `microsoft.com` → `Microsoft`
- `gdg.community.dev` or `google.com` → `Google`
- `aicamp.ai` → `AI Camp`
- Others → Extracted from domain name

---

## Filtering Flow

```
Corporate URL
    ↓
Scrape HTML
    ↓
Filter: Is this page a blog post/list?
    ↓ (No)
Extract Events (HTML links + JSON-LD)
    ↓
Filter: Is each extracted item a blog post/list?
    ↓ (No)
Include in Results
    ↓
Final Filter: Filter tech events (scoring system)
    ↓
Display with source="Customized"
```

---

## Usage

### Adding URLs
Simply add URLs to `Corporate_events.txt`, one per line:
```
https://gdg.community.dev/gdg-cloud-boston/
https://www.aicamp.ai/event/events
https://developer.nvidia.com/community
```

### Running Search
The corporate events scraping is automatically included when running:
```python
searcher = EnhancedTechComputingSearcher()
events = searcher.search_events(max_results=30)
```

Events from corporate URLs will appear with `source: "Customized"` in the results.

---

## Testing

### Blog Post Filter Test Results:
- ❌ "Top 10 AI Conferences in 2026" → Filtered out
- ✅ "Workshop: Machine Learning Fundamentals" → Included
- ❌ "5 Best Conferences You Must Attend" → Filtered out
- ✅ "NVIDIA GTC 2026" → Included

### URL Loading Test:
- Successfully loads all URLs from `Corporate_events.txt`
- Handles empty lines and comments
- Validates URL format

---

## Error Handling

- **File not found**: Warning message, continues without corporate events
- **HTTP errors**: Logs error, continues with next URL
- **Parsing errors**: Logs error, continues with next event
- **Invalid dates**: Events without valid future dates are skipped
- **Duplicate URLs**: Deduplicated in final filtering

---

## Future Enhancements

Potential improvements:
1. **Site-specific scrapers**: Custom extraction logic for specific sites (GDG, NVIDIA, etc.)
2. **Pagination support**: Handle multi-page event listings
3. **Rate limiting**: Respect robots.txt and add delays between requests
4. **Caching**: Cache scraped content to avoid repeated requests
5. **Better date extraction**: Site-specific date parsing patterns

---

## Summary

✅ **Added**: Corporate events scraping from `Corporate_events.txt`
✅ **Categorized**: All events from corporate URLs have `source: "Customized"`
✅ **Filtered**: Blog posts and list articles are automatically excluded
✅ **Integrated**: Works seamlessly with existing search pipeline
✅ **Robust**: Handles errors gracefully and continues processing

The system now has 5 sources:
1. RSS Feeds
2. Eventbrite
3. Tavily
4. Meetup Groups
5. **Corporate Events (Customized)** ← NEW

