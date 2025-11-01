# Event Filtering Investigation & Improvements

## Summary of Findings and Fixes

### Issues Investigated
1. **Eventbrite returning 0 events**
2. **Tech RSS Feeds (Google/Microsoft) returning 0 events**
3. **RSS/Meetup events being filtered out by scoring system**

---

## 1. Eventbrite Investigation

### Findings
- **Discovery page scraping**: ✅ Working - Found 184 event IDs in HTML
- **API calls**: ✅ Working - Successfully fetching event details
- **Filtering issue**: ❌ Too strict - Required ALL of:
  - `is_free = True`
  - Contains workshop/webinar/training keywords
  - Boston/Cambridge OR virtual

### Test Results
- Tested 10 events from Eventbrite discovery page:
  - **5/10** were free
  - **3/10** were workshop-type
  - **0/10** met ALL criteria (free + workshop + Boston/virtual)

### Solution Implemented
**Relaxed filtering criteria:**
- Changed from: `(free AND workshop AND Boston/virtual)`
- To: `((free OR workshop) AND Boston/virtual)`
- Allows:
  - Free events (even if not explicitly workshops)
  - Workshop-type events (even if paid)
  - Must still be in Boston/Cambridge or virtual

### Results
- **Before**: 0 events
- **After**: 1 event found and saved
- Example: "Lunch & Learn: Technology Trends Transforming Corporate Finance" (Free, Boston)

---

## 2. Tech RSS Feeds Investigation

### Findings
Tested the following feeds:
- `https://developers.google.com/events/feed` → **0 entries**
- `https://cloud.google.com/events/feed` → **0 entries**
- `https://techcommunity.microsoft.com/events/feed` → **0 entries`

### Root Cause
These feeds either:
1. Don't exist (404 or empty)
2. Return 0 entries (no events published)
3. Are not actual event feeds (might be blog feeds)

### Solution Implemented
- **Commented out** the Google/Microsoft feeds since they return 0 entries
- **Kept** Meetup RSS feeds which are working (24 events found)
- Added documentation explaining why they were removed

### Current RSS Sources
- **15 Meetup RSS feeds** from Boston tech groups
- **Working**: `bostonpython`, `Boston-Machine-Learning`, `Boston-AI`, etc.
- **Result**: 24 events found from Meetup RSS

---

## 3. RSS/Meetup Events Being Filtered Out

### Findings
- **24 RSS events found** initially
- **5 unique events** after deduplication
- **5 events** in final results

### Why Only 5 Events?

#### Deduplication (24 → 5)
- Many Meetup events are **recurring** (e.g., "Python Over Coffee" every Sunday)
- Deduplication removes events with >70% word overlap
- This is **correct behavior** - we don't want duplicate entries

#### Date Validation (Fixed)
- **Issue**: `_is_future_event()` was checking text patterns instead of actual dates
- **Fix**: Updated to check event date field first, then fall back to text patterns
- **Result**: Now correctly validates events with ISO dates like `2025-11-02`

#### Scoring System (Improved)
- **Issue**: RSS events scored lower than Tavily events (which have explicit "free workshop" keywords)
- **Fix**: 
  - Added +40 points bonus for RSS/curated sources
  - Added +30 points for Meetup RSS events (assuming they're meetups)
  - Added +20 points for MA/Virtual locations in Meetup events
  - Reduced penalty for paid RSS events (-10 instead of -30)

#### Slot Reservation (Implemented)
- **Issue**: Tavily events dominated top 30 slots due to high scores
- **Fix**: 
  - Reserve **40% slots** (8-20 events) for RSS/Eventbrite sources
  - Reserve **60% slots** for Tavily
  - Ensures representation from curated sources

### Results
- **Before**: 1 Meetup RSS event
- **After**: 5 Meetup RSS events
- **Improvement**: 5x increase in RSS representation

---

## Final Event Distribution

### Current Results (after all improvements)
```
Eventbrite:   1 event  (was 0)
Meetup RSS:   5 events (was 1)
Tavily:      29 events (consistent)
Total:       35 events
```

### Why This Distribution?

1. **Eventbrite (1 event)**
   - Relaxed filtering allows free OR workshop-type events
   - Still requires Boston/virtual location
   - Many events are paid conferences (excluded)
   - Some free events don't have workshop keywords (excluded)

2. **Meetup RSS (5 events)**
   - 24 events found from feeds
   - 19 filtered out as duplicates (recurring events)
   - 5 unique events remain
   - All 5 pass validation and are included

3. **Tavily (29 events)**
   - 33 events found
   - 4 filtered out (past dates, excluded URLs, low scores)
   - 29 high-quality events remain

---

## Key Improvements Made

### 1. Eventbrite Filtering
```python
# Before: Strict AND logic
if not is_free: continue
if not is_workshop: continue
if not (is_virtual or is_boston): continue

# After: Relaxed OR logic
if not (is_virtual or is_boston): continue  # Must be local/virtual
if is_free or is_workshop:  # Accept if free OR workshop-type
    if not is_free and not is_workshop:
        continue  # Paid non-workshops still excluded
```

### 2. Date Validation
```python
# Before: Only checked text patterns
def _is_future_event(self, text: str) -> bool:
    # Check for keywords like "upcoming", "future", etc.

# After: Check actual date first
def _is_future_event(self, text: str, event_date: str = None) -> bool:
    if event_date:
        # Parse and compare actual dates
        event_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
        return event_dt >= today
    # Fall back to text patterns if no date
```

### 3. Scoring System
```python
# Added bonuses for RSS sources:
+40 points: RSS/curated sources
+30 points: Meetup RSS events (assumed to be meetups)
+20 points: MA/Virtual locations for Meetup events
-10 points: Paid RSS events (reduced from -30)
```

### 4. Slot Reservation
```python
# Reserve 40% slots for RSS/Eventbrite (curated sources)
# Reserve 60% slots for Tavily (broad search)
# Ensures diversity in event sources
```

---

## Recommendations for Further Improvement

### Eventbrite
- **Current**: Finds 1 event (very strict)
- **Option 1**: Expand location to nearby cities (Cambridge, Somerville, etc.)
- **Option 2**: Allow paid workshops if explicitly hands-on
- **Option 3**: Increase number of events checked (currently limited to 15 per page)

### Meetup RSS
- **Current**: 5 unique events (after deduplication)
- **Note**: This is expected - many are recurring events (same title, different dates)
- **Option**: Consider grouping recurring events differently in UI

### Tech RSS Feeds
- **Current**: Google/Microsoft feeds return 0 entries
- **Option**: Find alternative event feeds from these companies
- **Alternative**: Manually curate major tech company events

---

## Conclusion

All three improvements have been implemented:
1. ✅ **Eventbrite**: Now finds 1 event (was 0) - relaxed filtering works
2. ✅ **Tech RSS Feeds**: Removed non-working feeds - documented why
3. ✅ **RSS Scoring**: Improved scoring and slot reservation - 5 events (was 1)

**Total improvement**: 35 events from 3 sources (was 30 from 1 source)

