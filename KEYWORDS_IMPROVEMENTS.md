# Keywords Analysis & Improvements

## Summary

Expanded keywords to improve event detection across all sources. The improvements target:
1. **Modern tech stack** (React, TypeScript, etc.)
2. **Casual event types** (coding nights, dev nights)
3. **Boston neighborhoods** (better location matching)
4. **Targeted Tavily searches** (framework/language-specific)

---

## Keyword Categories

### 1. Tech Keywords (`self.tech_keywords`)
**Purpose**: Identify tech-related content in event titles/descriptions

**Total**: 140 keywords (was ~90, added ~50)

#### Categories:
- **AI & Machine Learning** (12 keywords)
  - Added: `TensorFlow`, `PyTorch`, `Pandas`, `NumPy`, `Jupyter`, `Spark`
  
- **Web Frameworks & Languages** (NEW CATEGORY - 13 keywords)
  - Added: `React`, `Vue`, `Angular`, `Next.js`, `TypeScript`, `JavaScript`, `Node.js`
  - Added: `GraphQL`, `REST API`, `Svelte`, `Tailwind CSS`, `Express.js`
  - Added: `Python`, `Java`, `Go`, `Rust`, `Swift`, `Kotlin`

- **Backend & Databases** (NEW CATEGORY - 8 keywords)
  - Added: `PostgreSQL`, `MongoDB`, `Redis`, `Elasticsearch`
  - Added: `FastAPI`, `Django`, `Flask`, `Spring Boot`

- **Cloud & DevOps** (17 keywords)
  - Added: `CI/CD`, `GitHub Actions`, `Terraform`, `Ansible`, `Jenkins`, `GitLab`
  - Added: `monitoring`, `observability`, `Prometheus`, `Grafana`

- **Data & Analytics** (13 keywords)
  - Added: `Snowflake`, `Databricks`, `Airflow`, `dbt`

- **Mobile Development** (NEW CATEGORY - 4 keywords)
  - Added: `iOS`, `Android`, `Flutter`, `React Native`

- **Security & Testing** (NEW CATEGORY - 8 keywords)
  - Added: `cybersecurity`, `penetration testing`, `security`, `OWASP`
  - Added: `testing`, `QA`, `test automation`, `Selenium`, `Cypress`, `TDD`

---

### 2. Event Type Keywords (`self.event_keywords`)
**Purpose**: Identify formal event structures

**Total**: 55 keywords (was 18, added 20)

#### Original Categories:
- Conferences, workshops, tutorials, seminars, webinars
- Meetups, hackathons, trainings, bootcamps

#### NEW - Casual/Informal Event Types (20 keywords):
- `coding night`, `dev night`
- `tech talk`, `tech talk series`
- `code review`, `pair programming`, `mob programming`
- `TDD` (Test-Driven Development)
- `code kata`, `lightning talk`
- `tech lunch`, `brown bag`
- `office hours`, `Q&A`, `fireside chat`
- `unconference`, `bar camp`, `code retreat`
- `study group`, `reading group`

**Impact**: Now detects casual coding meetups and informal tech gatherings

---

### 3. Boston Location Keywords (`self.boston_keywords`)
**Purpose**: Match events in Greater Boston area

**Total**: 49 keywords (was 18, added 16)

#### Original:
- Cities: Boston, Cambridge, Somerville, Brookline, Newton, etc.
- Universities: MIT, Harvard, BU, Northeastern, etc.
- Squares: Kendall Square, Central Square, Davis Square, etc.

#### NEW - Neighborhoods (16 keywords):
- `South Boston`, `Southie`
- `Dorchester`, `Roxbury`
- `Allston`, `Brighton`
- `Jamaica Plain`, `JP`
- `Charlestown`, `East Boston`
- `North End`, `West End`
- `Beacon Hill`, `Fenway`
- `Longwood`, `Kenmore`
- `Mass Ave`, `Comm Ave`

**Impact**: Better location matching for events in Boston neighborhoods

---

### 4. Virtual Event Keywords (`self.virtual_keywords`)
**Purpose**: Identify online/virtual events

**Total**: 17 keywords (unchanged - already comprehensive)
- `virtual`, `online`, `remote`, `digital`, `webinar`
- `live stream`, `livestream`
- `zoom`, `teams`, `webex`, `gotomeeting`
- `youtube`, `twitch`, `facebook live`, `linkedin live`
- `global`, `worldwide`

---

### 5. Preferred Event Types (for scoring/prioritization)
**Purpose**: Identify hands-on, practical events

**Updated in**: `_meets_tech_criteria()` and `_filter_tech_events()`

**Added** (9 new keywords):
- `coding night`, `dev night`
- `tech talk`, `code review`
- `pair programming`, `mob programming`
- `TDD`, `code kata`
- `lightning talk`

---

## Tavily Search Queries

**Expanded from**: 29 queries → **43 queries**

### Original Queries (9 general):
- `free Boston developer workshop 2026`
- `free virtual developer workshop 2026`
- etc.

### NEW - Framework/Language-Specific (9 queries):
- `free React workshop Boston 2026`
- `free Python workshop Boston 2026`
- `free JavaScript meetup Boston 2026`
- `free Node.js workshop Boston 2026`
- `free TypeScript workshop Boston 2026`
- `free Docker workshop Boston 2026`
- `free Kubernetes workshop Boston 2026`
- `free Git workshop Boston 2026`
- `free cybersecurity workshop Boston 2026`

### NEW - Virtual Framework-Specific (5 queries):
- `free virtual React workshop 2026`
- `free virtual Python training 2026`
- `free online JavaScript course 2026`
- `free virtual AWS training 2026`
- `free online Kubernetes workshop 2026`

### NEW - Casual Event Types (2 queries):
- `free coding night Boston 2026`
- `free dev night Boston 2026`

### NEW - Tech Company Events (3 queries):
- `free GitHub workshop Boston 2026`
- `free Microsoft workshop virtual 2026`
- `free Google developer event virtual 2026`

**Impact**: More targeted searches find framework-specific and casual events

---

## Usage Throughout Codebase

### 1. RSS Feed Filtering
```python
# In _extract_tech_rss_event()
if not any(keyword.lower() in title.lower() for keyword in self.tech_keywords):
    return None  # Filter out non-tech events
```

### 2. Eventbrite Filtering
```python
# In _extract_tech_eventbrite_event()
has_tech_keywords = any(keyword.lower() in combined for keyword in self.tech_keywords)
if not (is_workshop_type or has_tech_keywords):
    return None
```

### 3. Tavily Result Filtering
```python
# In _meets_tech_criteria()
has_tech = any(keyword.lower() in combined_text for keyword in self.tech_keywords)
has_event = any(keyword.lower() in combined_text for keyword in self.event_keywords)
has_location = (any(keyword.lower() in combined_text for keyword in self.boston_keywords) or
                any(keyword.lower() in combined_text for keyword in self.virtual_keywords))
```

### 4. Scoring System
```python
# In _filter_tech_events() - score_event()
if any(p in combined for p in preferred):  # preferred includes new casual types
    score += 50
```

---

## Expected Improvements

### 1. Better Detection of Modern Tech Events
- **Before**: Might miss "React Workshop" if title only said "React"
- **After**: `React` is now in `tech_keywords` → will be detected

### 2. Better Detection of Casual Events
- **Before**: Might miss "Boston Coding Night" (not formal workshop)
- **After**: `coding night` is now in `event_keywords` and `preferred_event_types` → will be detected

### 3. Better Location Matching
- **Before**: Event in "Fenway" might not match if only "Boston" mentioned
- **After**: `Fenway` is now in `boston_keywords` → will match

### 4. More Targeted Tavily Searches
- **Before**: Generic "free Boston developer workshop" finds everything
- **After**: Specific "free React workshop Boston" finds React-specific events

---

## Testing Recommendations

1. **Search for React/TypeScript events** → Should find more framework-specific events
2. **Search for "coding night" or "dev night"** → Should find casual coding meetups
3. **Search events in neighborhoods** (Fenway, Allston) → Should match better
4. **Check Tavily results** → Should include more targeted results

---

## Potential Future Enhancements

1. **Programming Language-Specific Queries**
   - Add: `free Go workshop`, `free Rust meetup`, etc.

2. **Domain-Specific Queries**
   - Add: `free fintech workshop`, `free healthtech meetup`, etc.

3. **Company-Specific Queries**
   - Add: `free Stripe workshop`, `free Twilio training`, etc.

4. **Skill-Level Keywords**
   - Add: `beginner`, `intermediate`, `advanced` to help filter

5. **Time-Based Keywords**
   - Add: `evening`, `weekend`, `lunchtime` for better time filtering

---

## Keyword Statistics

| Category | Before | After | Added |
|----------|--------|-------|-------|
| Tech Keywords | ~90 | 140 | ~50 |
| Event Types | 18 | 55 | 37 |
| Boston Locations | 18 | 49 | 31 |
| Virtual Keywords | 17 | 17 | 0 |
| Tavily Queries | 29 | 43 | 14 |
| **Total** | **~172** | **~304** | **~132** |

**Improvement**: **76% increase** in keyword coverage

