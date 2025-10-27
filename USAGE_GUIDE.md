# AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area - Usage Guide

## 🎯 **Two Use Cases**

### **Use Case 1: Fresh Scraping + Load Data**
When you want to scrape new events from all websites and load them into the app.

### **Use Case 2: Load Existing Data Only**
When you want to quickly start the app with previously scraped data without re-scraping.

---

## 🚀 **Use Case 1: Fresh Scraping + Load Data**

### **Step 1: Start with Background Scraping**
```bash
# Activate virtual environment
source aiplusbio/bin/activate

# Start the app (automatically scrapes every 6 hours)
python run.py
```

### **Step 2: Manual Scraping (Optional)**
The app automatically scrapes every 6 hours, but you can trigger it manually:

**Via Web Interface:**
1. Go to http://localhost:5001
2. Click the "Refresh Events" button

**Via API:**
```bash
curl -X POST http://localhost:5001/api/scrape
```

### **Step 3: View Results**
- Open http://localhost:5001 in your browser
- Events will appear in the left panel
- Use search and filters to explore

---

## 🔄 **Use Case 2: Load Existing Data Only**

### **Option A: Quick Start (Recommended)**
```bash
# Activate virtual environment
source aiplusbio/bin/activate

# Start with existing data only
python quick_start.py
```

### **Option B: Manual Control**
```bash
# Activate virtual environment
source aiplusbio/bin/activate

# Start without background scraping
python app_no_scraping.py
```

### **Manual Scraping When Needed**
If you want to scrape new data later:
1. Click "Refresh Events" button in the web interface
2. Or use: `curl -X POST http://localhost:5001/api/scrape`

---

## 📊 **How to Use the Web Interface**

### **Main Features**

1. **Event List (Left Panel)**
   - Events are sorted by date (today → future)
   - Each event shows: title, date, time, location, type badges
   - Click any event for detailed information

2. **Search & Filters**
   - **Search Box**: Type keywords to filter events
   - **Computer Science Filter**: Show only CS events
   - **Biology Filter**: Show only biology events
   - **Event Count**: Shows how many events match your filters

3. **Event Details**
   - Click any event to see full information
   - Includes: description, registration info, source website
   - Direct link to original event page

4. **Google Calendar (Right Panel)**
   - Embedded Google Calendar
   - Events are displayed chronologically
   - Easy to add events to your personal calendar

### **Action Buttons**

- **Refresh Events**: Manually trigger scraping
- **Stats**: View scraping statistics and activity logs

---

## 🔧 **API Endpoints**

### **Get Events**
```bash
# Get all events
curl http://localhost:5001/api/events

# Get events with search filter
curl "http://localhost:5001/api/events?search=machine%20learning"

# Get only computer science events
curl "http://localhost:5001/api/events?cs=true"

# Get only biology events
curl "http://localhost:5001/api/events?biology=true"
```

### **Trigger Scraping**
```bash
curl -X POST http://localhost:5001/api/scrape
```

### **Get Statistics**
```bash
curl http://localhost:5001/api/stats
```

---

## 📁 **File Structure**

```
aiplusbio_website/
├── app.py                 # Main app with background scraping
├── app_no_scraping.py     # App without background scraping
├── quick_start.py         # Quick start script
├── run.py                 # Main startup script
├── database.py            # Database management
├── event_scraper.py       # Web scraping engine
├── event_categorizer.py   # AI categorization
├── websites_to_watch.txt  # List of websites to monitor
├── events.db              # SQLite database (created automatically)
├── templates/             # HTML templates
├── static/                # CSS and JavaScript files
└── README.md              # Main documentation
```

---

## 🎯 **Recommended Workflow**

### **First Time Setup**
1. Run `python run.py` to scrape initial data
2. Wait for scraping to complete (may take a few minutes)
3. Access http://localhost:5001 to view events

### **Daily Use**
1. Run `python quick_start.py` for fast startup
2. Use existing data for browsing and searching
3. Click "Refresh Events" when you want fresh data

### **Weekly Maintenance**
1. Run `python run.py` to get fresh data
2. Check "Stats" to see scraping activity
3. Review and clean up old events if needed

---

## 🚨 **Troubleshooting**

### **Port Already in Use**
If you see "Address already in use":
```bash
# Find and kill the process
lsof -ti:5001 | xargs kill -9

# Or use a different port
python app_no_scraping.py  # This will use port 5001
```

### **No Events Showing**
1. Check if scraping completed: Click "Stats" button
2. Manually trigger scraping: Click "Refresh Events"
3. Check browser console for errors

### **OpenAI API Issues**
- The app automatically falls back to keyword matching
- Events will still be categorized, just not with AI
- Check your OpenAI API quota and billing

---

## 💡 **Tips & Tricks**

1. **Bookmark the URL**: http://localhost:5001
2. **Use Search**: Try terms like "machine learning", "genomics", "seminar"
3. **Filter by Category**: Use checkboxes to focus on specific areas
4. **Check Stats**: Monitor scraping activity and success rates
5. **Export Events**: Use the API to get event data in JSON format

---

## 🔄 **Data Management**

### **Database Location**
- Events are stored in `events.db` (SQLite)
- Automatically created on first run
- Contains events, categories, and scraping logs

### **Data Retention**
- Events older than 30 days are automatically cleaned up
- You can modify this in `database.py`

### **Backup**
```bash
# Backup your database
cp events.db events_backup.db

# Restore from backup
cp events_backup.db events.db
``` 