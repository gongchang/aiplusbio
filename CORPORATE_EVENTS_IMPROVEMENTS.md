# Corporate Events Scraping Improvements

## Summary of Changes

Enhanced the corporate events scraping to follow links from starting URLs and extract detailed event information. Also added "Customized" as a filter option in the web interface.

---

## Improvements Made

### 1. ✅ Link Following Logic

**Problem**: Starting URLs in `Corporate_events.txt` are usually listing pages, not individual events.

**Solution**: Added `_find_event_links()` method that:
- Finds links containing event-related keywords (`event`, `workshop`, `webinar`, `conference`, `training`)
- Identifies links in event containers (divs with class/id containing "event")
- Filters out blog/news/article URLs
- Limits to same domain or subdomains
- Normalizes relative URLs to absolute URLs

**Link Patterns Detected**:
```regex
- /events/workshop-2026
- /conference/ai-summit
- /training/ml-bootcamp
- Links with event-related classes/IDs
- Calendar-style date URLs (YYYY/MM/)
```

### 2. ✅ Detailed Event Page Scraping

**Problem**: Individual event pages weren't being scraped for full details.

**Solution**: Added `_scrape_event_detail_page()` that:
- Fetches each event link found
- Filters out blog posts at the page level
- Extracts comprehensive event information
- Returns detailed event objects

**Method**: `_scrape_event_detail_page(event_url, source_url, headers)`

### 3. ✅ Comprehensive Event Extraction

**Problem**: Previous extraction was limited to basic HTML links.

**Solution**: Added `_extract_event_from_detail_page()` that:

**Priority Order**:
1. **JSON-LD Structured Data** (most reliable)
   - Parses `<script type="application/ld+json">`
   - Handles both single objects and arrays
   - Extracts: name, description, startDate, location, etc.

2. **HTML Structure Extraction** (fallback)
   - Extracts title from `<title>` or `<h1>` tags
   - Extracts description from meta tags or content divs
   - Extracts date from multiple patterns
   - Validates tech keywords and event types

**Date Extraction Patterns**:
- `<time datetime="...">`
- `class="date"` or `id="date"`
- Text patterns: "January 15, 2026", "1/15/2026", "2026-01-15"

### 4. ✅ Enhanced Description Extraction

**Problem**: Event descriptions weren't being captured well.

**Solution**: Added `_extract_description_from_detail_page()` that tries:
1. Meta description tag
2. JSON-LD description field
3. Common content containers (divs with "description" or "content" classes)

### 5. ✅ Multi-Level Blog Post Filtering

**Problem**: Blog posts still appearing in results.

**Solution**: Applied filtering at 3 levels:
1. **Page-level**: Filter entire listing pages that are blog posts
2. **Link-level**: Filter individual event links that point to blog posts
3. **Final filter**: Filter in `_filter_tech_events()` before scoring

**Blog Post Indicators**:
- Title patterns: "top 10", "best 5", "list of", "guide to"
- URL patterns: `/blog/`, `/article/`, `/news/`
- Description patterns: Multiple numbered items (1., 2., 3.)

### 6. ✅ Web Interface Filter

**Problem**: "Customized" source wasn't visible as a filter option.

**Solution**: Added checkbox filter in `computing_events.html`:
```html
<div class="form-check">
    <input class="form-check-input source-checkbox" type="checkbox" 
           id="sourceCustomized" value="Customized" checked>
    <label class="form-check-label" for="sourceCustomized">
        <i class="fas fa-building me-1"></i> Customized
    </label>
</div>
```

---

## Workflow

### Before (Simple):
```
Starting URL → Extract links from page → Done
```

### After (Comprehensive):
```
Starting URL
    ↓
Step 1: Extract events directly from listing page
    ↓
Step 2: Find event links (15 max per starting URL)
    ↓
Step 3: For each event link:
    - Fetch event detail page
    - Check if blog post (skip if yes)
    - Extract detailed event info (JSON-LD → HTML fallback)
    - Validate: tech keywords + event type + future date
    ↓
Step 4: Deduplicate by URL
    ↓
Step 5: Filter blog posts (final pass)
    ↓
Step 6: Integrate with existing filtering/scoring
    ↓
Display with source="Customized"
```

---

## New Methods Added

1. **`_find_event_links(html, source_url)`**
   - Finds potential event links from HTML
   - Returns list of URLs to follow

2. **`_scrape_event_detail_page(event_url, source_url, headers)`**
   - Fetches and scrapes individual event pages
   - Filters blog posts before extraction

3. **`_extract_event_from_detail_page(html, event_url, source_url)`**
   - Extracts comprehensive event information
   - Tries JSON-LD first, then HTML structure
   - Validates tech relevance and event type

4. **`_extract_description_from_detail_page(html)`**
   - Extracts event descriptions using multiple methods
   - Returns best available description

5. **`_extract_date_from_detail_page(html, title)`**
   - Extracts dates using multiple patterns
   - Tries JSON-LD, HTML time tags, text patterns
   - Validates future dates

---

## Configuration

### Link Following Limits
- **15 links per starting URL**: Prevents excessive requests
- **15 second timeout per page**: Fast failure for slow sites
- **Same domain restriction**: Only follows links within the same domain/subdomain

### Filtering Criteria
Events are included only if:
- ✅ Has valid future date
- ✅ Contains tech keywords (ML, AI, DevOps, etc.)
- ✅ Contains event type keywords (workshop, conference, etc.)
- ✅ Not a blog post/list article
- ✅ Not excluded URL (from `websites_to_watch.txt`)

---

## Expected Results

### Before:
- ❌ 0 events found (only checked starting page)
- ❌ No link following
- ❌ Limited extraction from listing pages

### After:
- ✅ Events found from both listing pages AND individual event pages
- ✅ Comprehensive information extraction
- ✅ Better date/time/location details
- ✅ "Customized" filter available in web interface
- ✅ Blog posts filtered at multiple levels

---

## Testing

### Test Cases:
1. **GDG Cloud Boston**: Should find events from event listing + individual event pages
2. **AI Camp Events**: Should extract from structured event listings
3. **NVIDIA Community**: Should find community events
4. **Microsoft Events Catalog**: Should extract from search results

### Verification:
```python
# All methods verified:
✅ _find_event_links() - Finds event links correctly
✅ _scrape_event_detail_page() - Scrapes detail pages
✅ _extract_event_from_detail_page() - Extracts comprehensive info
✅ _extract_description_from_detail_page() - Gets descriptions
✅ _extract_date_from_detail_page() - Extracts dates
✅ _is_blog_post_list() - Filters blog posts

# Integration verified:
✅ Integrated into search_events()
✅ Customized filter in web interface
✅ Source set to "Customized"
```

---

## Usage

### Adding Corporate URLs
Simply add starting URLs to `Corporate_events.txt`:
```
https://gdg.community.dev/gdg-cloud-boston/
https://www.aicamp.ai/event/events
https://developer.nvidia.com/community
```

The system will:
1. Load the starting URL
2. Extract any direct events
3. Find and follow links to individual event pages
4. Extract detailed information
5. Filter and categorize as "Customized"

### Filtering in Web Interface
Users can now filter by source, including:
- ✅ Tavily
- ✅ Meetup RSS
- ✅ Eventbrite
- ✅ Tech RSS Feed
- ✅ **Customized** ← NEW

---

## Error Handling

- **HTTP errors**: Silently skip and continue with next link
- **Parsing errors**: Skip event, continue processing
- **Timeout**: Skip slow pages, continue with others
- **Invalid dates**: Skip events without valid future dates
- **Blog posts**: Filtered at multiple levels

---

## Performance Considerations

- **Rate limiting**: 15 links per starting URL prevents overload
- **Timeout**: 15 seconds per page for fast failure
- **Caching**: Not implemented (can be added if needed)
- **Parallel requests**: Sequential (can be optimized with async)

---

## Future Enhancements

1. **Site-specific scrapers**: Custom logic for known sites (GDG, NVIDIA, etc.)
2. **Pagination support**: Follow "next page" links in listings
3. **Rate limiting**: Respect robots.txt and add delays
4. **Caching**: Cache scraped content to avoid repeated requests
5. **Parallel scraping**: Use async/threading for faster processing
6. **Better date extraction**: Machine learning for date parsing
7. **Location extraction**: Better location parsing from various formats

---

## Summary

✅ **Link Following**: Now follows links from starting URLs to find individual events
✅ **Detailed Extraction**: Comprehensive event information from detail pages
✅ **Multi-level Filtering**: Blog posts filtered at multiple stages
✅ **Web Interface**: "Customized" filter added to source filters
✅ **Better Results**: More events found with complete information
✅ **Robust Error Handling**: Graceful failures, continues processing

The corporate events scraping is now much more comprehensive and should find significantly more events from the starting URLs.

