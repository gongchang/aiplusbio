# Computing Events: Filtering and Scoring Logic

## Event Sources

The computing events page aggregates events from **4 main sources**:

### 1. **Tavily** (Primary Source)
- **Type**: AI-powered web search API
- **Description**: Searches the web for free tech workshops, webinars, trainings, and one-day conferences
- **Focus**: Virtual and Boston-local events
- **Queries Used**: 29 targeted search queries including:
  - "free Boston developer workshop 2026"
  - "free virtual AI webinar 2026"
  - "free one day tech conference Boston 2026"
  - "free Boston hackathon 2026"
  - etc.

### 2. **Meetup RSS**
- **Type**: RSS feeds from Boston tech Meetup groups
- **Description**: Individual event-level RSS feeds from verified Boston tech Meetup groups
- **Groups Included**:
  - Boston Python (`bostonpython`)
  - Boston Machine Learning
  - Boston Data Science
  - Boston AI
  - Boston Cloud Computing
  - Boston DevOps
  - Boston Startups
  - Boston Product Management
  - Boston Entrepreneurs
  - Boston Code and Coffee
  - Boston React
  - Cambridge Tech Meetup
  - Boston Software Craftsmanship
  - Boston JS
- **Date Extraction**: Fetches individual event pages to extract actual event dates

### 3. **Eventbrite**
- **Type**: Event discovery + API
- **Description**: Scrapes Eventbrite discovery pages to find event IDs, then uses API to get details
- **Method**: 
  1. Scrapes `https://www.eventbrite.com/d/ma--boston/technology--events/` and virtual pages
  2. Extracts event IDs from HTML (URLs and `data-event-id` attributes)
  3. Fetches event details via Eventbrite API
  4. Filters for: free + workshop/webinar/training + (Boston or virtual)

### 4. **Tech RSS Feed**
- **Type**: RSS feeds from major tech companies
- **Description**: Official event feeds from tech companies
- **Feeds Included**:
  - Google Developers Events (`https://developers.google.com/events/feed`)
  - Google Cloud Events (`https://cloud.google.com/events/feed`)
  - Microsoft Tech Community Events (`https://techcommunity.microsoft.com/events/feed`)

---

## Event Filtering Logic

### Initial Source-Level Filtering

Each source applies its own filtering before events are combined:

#### **Tavily Events**
- Must contain tech keywords (AI, ML, cloud, developer, coding, etc.)
- Must be future events
- Must be local (Boston/Cambridge) or virtual
- Prioritizes: free + workshop/webinar/training + hands-on events
- Excludes: Commercial conferences (unless explicitly free)

#### **Meetup RSS Events**
- All events from tech-focused Meetup groups are included (no keyword filtering needed)
- Must have valid future event date (extracted from event page if needed)
- Must have valid event-level URL

#### **Eventbrite Events**
- Must be `is_free = True`
- Title/description must contain: workshop, webinar, training, bootcamp, tutorial, meetup, hackathon, hands-on, developer, coding
- Must be virtual OR in Boston/Cambridge area

#### **Tech RSS Feed Events**
- Must contain tech keywords in title
- Must have valid future date
- Must have valid URL

### Combined Filtering (After Sources Merge)

After all sources are combined, additional filtering is applied:

1. **URL Exclusion**: Removes events from URLs in `websites_to_watch.txt` (to avoid duplicates with main page)
2. **Future Event Check**: Only events with future dates are kept
3. **Deduplication**: Removes duplicate events based on title similarity (>70% word overlap)
4. **Scoring and Ranking**: Events are scored and sorted (see Scoring Logic below)

---

## Event Scoring System

Events are scored based on multiple criteria to prioritize the most relevant events:

### Scoring Formula

```python
def score_event(event):
    score = 0
    
    # High priority: Free events (+100 points)
    if 'free' in title+description or cost == 'free':
        score += 100
    
    # High priority: Preferred event types (+50 points)
    # (workshop, webinar, training, bootcamp, tutorial, hands-on, 
    #  meetup, hackathon, coding challenge, one-day, one day)
    if any(preferred_type in title+description):
        score += 50
    
    # Priority: Boston local events (+30 points)
    if location contains Boston/Cambridge keywords:
        score += 30
    
    # Priority: Virtual events (+20 points)
    if is_virtual or 'virtual' in title+description:
        score += 20
    
    # Penalty: Commercial conferences (-50 points)
    if contains 'summit', 'expo', 'convention', '3-day', '4-day', '5-day' 
       AND not explicitly free:
        score -= 50
    
    # Penalty: Paid events without preferred type (-30 points)
    if cost is not 'free' and no preferred type:
        score -= 30
    
    return score
```

### Scoring Breakdown

| Criteria | Points | Notes |
|----------|--------|-------|
| **Free event** | +100 | Highest priority - free events are preferred |
| **Preferred type** | +50 | Workshop, webinar, training, bootcamp, tutorial, hands-on, meetup, hackathon, coding challenge, one-day events |
| **Boston local** | +30 | Events in Boston, Cambridge, or Greater Boston area |
| **Virtual event** | +20 | Online/virtual events are accessible to all |
| **Commercial conference** | -50 | Penalty for paid multi-day conferences (unless explicitly free) |
| **Paid non-preferred** | -30 | Penalty for paid events that aren't workshops/trainings |

### Final Event Selection

1. **Sort by Score**: Events are sorted in descending order by score
2. **Apply Minimum Threshold**: Events with score < -20 are excluded (unless we need more events to fill the quota)
3. **Take Top N**: Select top `max_results` events (default: 30)

### Example Scores

**High-Scoring Events (170+ points):**
- Free Boston Python workshop (Free: +100, Workshop: +50, Boston: +30) = **180**
- Free virtual AI webinar (Free: +100, Webinar: +50, Virtual: +20) = **170**

**Medium-Scoring Events (50-120 points):**
- Free Boston meetup (Free: +100, Meetup: +50, Boston: +30) = **180** (but if no Boston keyword, = 150)
- Paid workshop in Boston (Workshop: +50, Boston: +30) = **80** (no free bonus)

**Low-Scoring Events (< 50 points):**
- Paid conference (no preferred type) = **0** (or -30 if commercial)
- Paid non-workshop event = **-30**
- Commercial paid conference = **-50**

---

## Filter Criteria Summary

### Must Have (Required)
- ✅ Tech-related content
- ✅ Valid future event date
- ✅ Valid event-level URL (not just listing page)
- ✅ Not from excluded URLs
- ✅ Not a duplicate

### Should Have (High Priority)
- ✅ **Free** (cost = "Free")
- ✅ **Preferred event type** (workshop, webinar, training, bootcamp, tutorial, hands-on, meetup, hackathon)
- ✅ **Local** (Boston, Cambridge, Greater Boston) OR **Virtual**

### Nice to Have (Bonus Points)
- ✅ Hands-on/practical focus
- ✅ One-day duration
- ✅ Developer/coding focus

### Avoid (Penalized/Excluded)
- ❌ Commercial paid conferences (unless explicitly free)
- ❌ Multi-day paid events
- ❌ Generic courses without event structure
- ❌ Past events
- ❌ Duplicate events

---

## User Interface Filters

The web interface provides the following filters:

### 1. **Search Box**
- Searches across: title, description, location
- Case-insensitive, partial matching

### 2. **Cost Type Filter**
- Free
- Paid
- Unknown

### 3. **Source Filter** (NEW)
- Tavily
- Meetup RSS
- Eventbrite
- Tech RSS Feed

### 4. **Host Filter**
- Dynamically populated from all unique hosts in events
- Allows filtering by event host/organizer

---

## Data Flow

```
1. Search Sources
   ├─ Tavily API (29 queries) → ~33 events
   ├─ Meetup RSS (18 feeds) → ~24 events
   ├─ Eventbrite (discovery scraping + API) → varies
   └─ Tech RSS (3 feeds) → varies
   
2. Source-Level Filtering
   └─ Each source filters before returning events
   
3. Combine & Deduplicate
   └─ Merge all events, remove duplicates
   
4. Score & Rank
   └─ Score each event, sort by score
   
5. Final Filtering
   └─ Apply minimum score threshold, take top N
   
6. Return to User
   └─ Display in calendar/list view with filters
```

---

## Notes

- **Date Extraction**: Uses `ImprovedDateExtractor` to parse dates from various formats
- **URL Validation**: Ensures all events have individual event-level URLs (not listing pages)
- **Future Events Only**: All events must have dates in the future
- **Boston Keywords**: Recognizes Boston, Cambridge, Somerville, Brookline, Newton, Waltham, Lexington, Arlington, Medford, Massachusetts, MA, Greater Boston, MIT, Harvard, BU, etc.
- **Virtual Keywords**: Recognizes virtual, online, remote, digital, webinar, live stream, zoom, teams, etc.

