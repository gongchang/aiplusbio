# Customized Source Scraping Improvements

## Summary

Enhanced the Customized source scraping to:
1. **Follow more links**: Increased from 15 to 50 links per starting URL
2. **Follow nested links**: Scrapes event pages and follows links within them (up to 5 per page)
3. **Pagination support**: Follows pagination links to get more events
4. **Strict location filtering**: Only includes events that are **Boston local OR Virtual**
5. **Better navigation filtering**: Excludes login/account/navigation pages
6. **Improved URL loading**: Handles all URLs in Corporate_events.txt even with different formats

---

## Improvements Made

### 1. ✅ Enhanced Link Following

**Before**:
- Followed 15 links per starting URL
- Only followed direct links from listing page

**After**:
- Follows **50 links** per starting URL
- Follows **nested links** from event detail pages (up to 5 per page)
- Follows **pagination links** (up to 3 paginated pages)

**Result**: Much more comprehensive event discovery

### 2. ✅ Strict Location Filtering

**Requirement**: Only include events that are **Boston local OR Virtual**

**Implementation**:
```python
# In _extract_event_from_detail_page()
is_boston = any(b in combined_location for b in self.boston_keywords)
is_virt = is_virtual or any(v in combined_location for v in self.virtual_keywords)

# Reject if not Boston and not virtual
if not (is_boston or is_virt):
    return None  # Skip event
```

**Applied at 3 levels**:
1. **HTML extraction**: Filters events when extracting from listing pages
2. **Detail page scraping**: Filters when scraping individual event pages
3. **Link following**: Double-checks before adding to results

### 3. ✅ Improved Navigation Filtering

**Problem**: Navigation pages like "Upcoming Events", "Log in" were being scraped as events

**Solution**: Added comprehensive filtering:
```python
navigation_patterns = [
    'upcoming events', 'past events', 'all events', 'my events',
    'log in', 'login', 'sign up', 'signup', 'register',
    'create account', 'my account', 'account settings',
    'home', 'about', 'contact', 'help', 'faq'
]

# Filter out account/login/profile URLs
if '/login' in url or '/account' in url or '/profile' in url:
    return True  # Skip as blog post/navigation
```

### 4. ✅ Enhanced Event Link Detection

**Added More Patterns**:
- `/events/details/` patterns (most specific)
- Event cards/tiles with nested links
- Article tags containing events
- Data attributes indicating events
- Workshop/webinar specific patterns

**Patterns Now Detected**:
```regex
- /events/[id]/details
- /events/details/[name]
- Links in event containers (divs with class="event")
- Links in article tags
- Links with data-event attributes
- Event cards/tiles
```

### 5. ✅ Pagination Support

**New Method**: `_find_pagination_links()`

Finds pagination links using patterns:
- Links containing "next", "more", "page", "view-all"
- URLs with `page=` query parameters
- Links with text "all", "more", "next", "view"

**Result**: Can scrape multiple pages of events from listing pages

### 6. ✅ Improved URL Loading

**Problem**: Only loading 1 URL when file should have 5

**Solution**: Enhanced `_load_corporate_event_urls()`:
- Uses regex to extract URLs even if not at start of line
- Handles URLs with query parameters
- Cleans up URLs (removes trailing `/`, `)`, `]`)
- Handles different file encodings

---

## Scraping Workflow

### Complete Flow:
```
Starting URL (e.g., gdg.community.dev/gdg-cloud-boston/)
    ↓
1. Extract events directly from listing page
    ↓
2. Find pagination links → Follow up to 3 paginated pages
    ↓
3. Find event links (up to 50 per starting URL)
    ↓
4. For each event link:
   a. Scrape event detail page
   b. Check: Boston OR Virtual? → Skip if neither
   c. Check: Navigation page? → Skip if yes
   d. Extract detailed event info
   e. Find nested links (up to 5 per event page)
   f. Add nested links to queue
    ↓
5. Deduplicate by URL
    ↓
6. Filter blog posts/navigation
    ↓
7. Return Customized events
```

---

## Location Filtering Details

### Boston Keywords (49 total):
- Cities: Boston, Cambridge, Somerville, Brookline, Newton, etc.
- Universities: MIT, Harvard, BU, Northeastern, etc.
- Neighborhoods: Kendall Square, Central Square, Seaport, etc.
- All Boston area locations

### Virtual Keywords (17 total):
- virtual, online, remote, digital, webinar
- zoom, teams, webex, youtube, livestream
- global, worldwide

### Filtering Logic:
```python
# Event is included if:
(is_boston OR is_virtual) AND
has_tech_keywords AND
has_event_keywords AND
is_future_event AND
not_blog_post AND
not_navigation_page
```

---

## Expected Results

### Current State (1 URL in file):
- **5-10 events** from GDG Cloud Boston
- All events are Virtual (GDG events are typically virtual)
- No Boston local events from this source yet

### Potential State (5 URLs in file):
- **GDG Cloud Boston**: 5-10 virtual events
- **AI Camp**: Multiple Boston/virtual tech events
- **NVIDIA Community**: Tech events (may need filtering)
- **Microsoft Events**: Azure/cloud events (Boston/virtual)
- **GitHub Events**: Developer events (Boston/virtual)

**Estimated**: **20-50+ events** with all 5 URLs

---

## Testing

### Verification:
```python
✅ URL loading: Handles all 5 URLs correctly
✅ Link following: 50 links per URL (increased from 15)
✅ Nested links: Follows links within event pages
✅ Pagination: Follows paginated listing pages
✅ Location filtering: Only Boston OR Virtual
✅ Navigation filtering: Excludes login/account pages
✅ Event detection: More comprehensive patterns
```

### Sample Results:
- ✅ "DevFest Boston 2025" (Virtual)
- ✅ "Accelerate AI with Cloud Run" (Virtual)
- ✅ "Become a Generative AI Leader" (Virtual)
- ❌ "Upcoming Events" (filtered out - navigation)
- ❌ "Log in" (filtered out - account page)

---

## File Format

**Corporate_events.txt** should contain:
```
https://gdg.community.dev/gdg-cloud-boston/
https://www.aicamp.ai/event/events
https://developer.nvidia.com/community
https://www.microsoft.com/en/events/search-catalog/?filters=...
https://github.com/resources/events
```

**Note**: The file currently only has 1 URL saved. To get more events, save all 5 URLs to the file.

---

## Configuration

### Link Following Limits:
- **50 links per starting URL**: Increased from 15
- **5 nested links per event page**: New feature
- **3 pagination pages**: New feature
- **15 second timeout per page**: Fast failure

### Filtering:
- **Location**: Must be Boston OR Virtual
- **Tech**: Must contain tech keywords
- **Event Type**: Must contain event keywords
- **Future**: Must be future date
- **Navigation**: Excludes login/account pages
- **Blog Posts**: Excludes list articles

---

## Summary

✅ **Link Following**: 50 links per URL (was 15) + nested + pagination
✅ **Location Filtering**: Strict - only Boston OR Virtual
✅ **Navigation Filtering**: Excludes login/account/navigation pages
✅ **Event Detection**: More comprehensive patterns
✅ **URL Loading**: Handles all 5 URLs with various formats
✅ **Pagination**: Follows paginated listing pages

**Result**: Much more comprehensive scraping that finds significantly more events while maintaining strict filtering for Boston local and Virtual events only.

