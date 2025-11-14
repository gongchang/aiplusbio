# AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area

A comprehensive web application that automatically scrapes and aggregates academic events from multiple MIT and Harvard websites, categorizes them using AI, and presents them in a modern web interface with Google Calendar integration.

## Features

### 🎯 **Smart Event Aggregation**
- Automatically scrapes events from 15+ academic websites
- Intelligent date and time extraction from various formats
- Detects virtual vs. on-site events automatically
- Identifies registration requirements

### 🤖 **AI-Powered Categorization**
- Uses OpenAI GPT-3.5 to categorize events into "Computer Science" and "Biology"
- Fallback keyword-based categorization if AI is unavailable
- Supports events that belong to multiple categories

### 🎨 **Modern Web Interface**
- Responsive design that works on desktop and mobile
- Real-time search and filtering capabilities
- Category-based filtering (CS/Biology)
- Event count and statistics dashboard

### 📅 **Google Calendar Integration**
- Embedded Google Calendar on the right panel
- Events are displayed in chronological order
- Easy to add events to your personal calendar

### ⚡ **Efficient Data Management**
- SQLite database with intelligent caching
- Background scraping every 6 hours
- Avoids re-scraping duplicate events
- Automatic cleanup of old events

## Screenshots

The application features a clean, modern interface with:
- **Left Panel**: Event list with filters and search
- **Right Panel**: Google Calendar integration
- **Responsive Design**: Works seamlessly on all devices

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key (optional, for AI categorization)

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd aiplusbio_website
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp config.env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the web interface**
   Open your browser and go to: `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables. When you
deploy, convert the same keys into Cloud Run / Cloud Functions environment
variables or secrets.

```env
# Core app configuration
FLASK_ENV=development
FLASK_DEBUG=True
USE_FIRESTORE=false          # Set to true in Cloud Run / Functions
GOOGLE_CLOUD_PROJECT=your-gcp-project-id

# External APIs used by the scrapers
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
Tavily_API=your-tavily-api-key   # Legacy alias used by older scripts
EVENTBRITE_API_KEY=your-eventbrite-api-key
LUMA_API_KEY=your-luma-api-key

# Local database fallback (set to /tmp/events.db in serverless environments)
DATABASE_PATH=events.db

# Scraping behaviour
SCRAPING_INTERVAL_HOURS=6
REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

### Adding New Websites

To add new websites to monitor, edit `websites_to_watch.txt`:

```txt
https://example.com/events
https://another-site.com/calendar
# Comments start with #
```

## Usage

### Web Interface

1. **View Events**: Events are automatically loaded and displayed in chronological order
2. **Search**: Use the search box to filter events by title, description, or location
3. **Filter by Category**: Check the Computer Science or Biology checkboxes to filter events
4. **View Details**: Click on any event to see detailed information
5. **Refresh**: Click "Refresh Events" to manually trigger scraping
6. **Statistics**: Click "Stats" to view scraping statistics and activity

### Updating the Virtual Worldwide Page

The Virtual Worldwide page is curated manually from `virtual_worldwide.txt`. When you add, remove, or reorder URLs in that list, run the helper script to regenerate the static HTML cards:

```bash
python tools/update_virtual_worldwide.py
```

This script reads every non-comment URL from `virtual_worldwide.txt` and rewrites `templates/virtual_worldwide.html` with a matching set of cards. There’s no runtime dependency—just run the script whenever you change the list, then reload the page.

### API Endpoints

The application provides several REST API endpoints:

- `GET /api/events` - Get all events with optional filtering
- `POST /api/scrape` - Manually trigger event scraping
- `GET /api/stats` - Get scraping statistics

### Example API Usage

```bash
# Get all events
curl http://localhost:5000/api/events

# Get events filtered by search term
curl "http://localhost:5000/api/events?search=machine%20learning"

# Get only computer science events
curl "http://localhost:5000/api/events?cs=true"

# Trigger manual scraping
curl -X POST http://localhost:5000/api/scrape
```

## Architecture

### Backend Components

- **`app.py`**: Main Flask application with API endpoints
- **`database.py`**: SQLite database management and queries
- **`event_scraper.py`**: Web scraping engine with multiple strategies
- **`event_categorizer.py`**: AI-powered event categorization

### Frontend Components

- **`templates/index.html`**: Main web interface
- **`static/css/style.css`**: Custom styling and responsive design
- **`static/js/app.js`**: Frontend JavaScript for interactivity

### Data Flow

1. **Scraping**: Background process scrapes websites every 6 hours
2. **Processing**: Events are parsed and categorized using AI/keywords
3. **Storage**: Events are stored in SQLite database with deduplication
4. **Serving**: Web interface serves events with real-time filtering
5. **Display**: Events are displayed in chronological order with rich metadata

## Supported Websites

The application currently monitors events from:

- MIT CSAIL Events
- MIT Schwarzman College of Computing
- MIT Biology Events
- MIT BE (Biological Engineering)
- Harvard SEAS Events
- Harvard Biostatistics Seminars
- Harvard Data Science Events
- Harvard CMSA Events
- Harvard Quantitative Genomics
- IAIFI Events
- MIT BCS Events
- MIT KI Events
- MIT WI Events
- MIT HST Events

## Customization

### Adding New Event Sources

1. Add the URL to `websites_to_watch.txt`
2. The scraper will automatically attempt to extract events
3. For complex sites, you may need to modify `event_scraper.py`

### Modifying Categories

Edit `event_categorizer.py` to:
- Add new categories
- Modify keyword lists
- Adjust AI prompts

### Styling Changes

Modify `static/css/style.css` to customize the appearance.

## Troubleshooting

### Common Issues

1. **No events showing up**
   - Check if scraping is working: click "Stats" button
   - Verify websites are accessible
   - Check browser console for errors

2. **AI categorization not working**
   - Verify OpenAI API key is set correctly
   - Check API quota and billing
   - The app will fall back to keyword matching

3. **Scraping errors**
   - Some websites may block automated requests
   - Check the scraping logs in the stats modal
   - Consider adjusting request delays

### Logs

The application logs scraping activity to the database. View recent activity in the Stats modal.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in the Stats modal
3. Open an issue on the repository

---

**Built with ❤️ for the AI+Bio research community** 

### Continuous Integration

A GitHub Actions workflow located at `.github/workflows/ci.yml` runs automatically on every push and pull request to `main`. It installs dependencies from `requirements.txt` and executes the full pytest suite to ensure the application remains stable.

```bash
# Execute locally to mirror CI
pip install -r requirements.txt
pytest
``` 

## Deploying on Google Cloud

### Overview
- **Cloud Run** hosts the Flask web UI (scales to zero, covered by the free tier).
- **Cloud Functions** runs the scraper on-demand.
- **Cloud Scheduler** triggers the scraper every 12 hours.
- **Firestore (Native mode)** stores event documents for both the web app and scraper.

### 1. Project bootstrap
```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  firestore.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Firestore (Native mode)
```bash
gcloud firestore databases create \
  --location=us-central1 \
  --type=firestore-native
```

### 3. Manage secrets
Store API keys in Secret Manager (recommended) or export them in the shell.
```bash
printf '%s' "$OPENAI_API_KEY"      | gcloud secrets create OPENAI_API_KEY --data-file=- --replication-policy=automatic
printf '%s' "$TAVILY_API_KEY"      | gcloud secrets create TAVILY_API_KEY --data-file=- --replication-policy=automatic
printf '%s' "$EVENTBRITE_API_KEY"  | gcloud secrets create EVENTBRITE_API_KEY --data-file=- --replication-policy=automatic
printf '%s' "$LUMA_API_KEY"        | gcloud secrets create LUMA_API_KEY --data-file=- --replication-policy=automatic
```

### 4. Build & deploy Cloud Run (web app)
```bash
export PROJECT_ID=<PROJECT_ID>
gcloud builds submit --tag gcr.io/$PROJECT_ID/aiplusbio-web
gcloud run deploy aiplusbio-web \
  --image gcr.io/$PROJECT_ID/aiplusbio-web \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=512Mi --cpu=1 \
  --concurrency=10 \
  --min-instances=0 --max-instances=1 \
  --set-env-vars USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,DATABASE_PATH=/tmp/events.db \
  --update-secrets \
      TAVILY_API_KEY=TAVILY_API_KEY:latest,\
      Tavily_API=TAVILY_API_KEY:latest,\
      EVENTBRITE_API_KEY=EVENTBRITE_API_KEY:latest,\
      LUMA_API_KEY=LUMA_API_KEY:latest,\
      OPENAI_API_KEY=OPENAI_API_KEY:latest
```

### 5. Deploy the scraper as a 2nd gen Cloud Function
`main.py` in the repo root exposes the required `scrape_http` entrypoint.
```bash
gcloud functions deploy scrape-http \
  --region=us-central1 \
  --runtime python312 \
  --trigger-http \
  --memory=256MB \
  --timeout=120s \
  --max-instances=1 \
  --entry-point scrape_http \
  --source=. \
  --set-env-vars USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,DATABASE_PATH=/tmp/events.db \
  --update-secrets \
      TAVILY_API_KEY=TAVILY_API_KEY:latest,\
      Tavily_API=TAVILY_API_KEY:latest,\
      EVENTBRITE_API_KEY=EVENTBRITE_API_KEY:latest,\
      LUMA_API_KEY=LUMA_API_KEY:latest,\
      OPENAI_API_KEY=OPENAI_API_KEY:latest
```

### 6. Schedule the scraper every 12 hours
```bash
gcloud iam service-accounts create scraper-scheduler

gcloud scheduler jobs create http scrape-events \
  --location=us-central1 \
  --schedule="0 */12 * * *" \
  --uri=https://us-central1-$PROJECT_ID.cloudfunctions.net/scrape-http \
  --http-method=POST \
  --oidc-service-account-email=scraper-scheduler@$PROJECT_ID.iam.gserviceaccount.com
```
Grant the scheduler service account `roles/cloudfunctions.invoker` and ensure
the Cloud Function’s runtime service account has `roles/datastore.user` and
`roles/logging.logWriter`.

### 7. Stay inside the free tier
- Use the smallest instance sizes shown above.
- Monitor Cloud Run, Cloud Functions, and Firestore usage in Cloud Monitoring.
- Call `EventStore.prune_older_than(days=90)` periodically to keep Firestore
  storage below 1 GB.
### 8. Testing the Google Cloud Deployment

#### Get Your Service URLs
```bash
# Get Cloud Run web app URL
gcloud run services describe aiplusbio-web --region=us-central1 --format='value(status.url)'

# Get Cloud Function scraper URL
gcloud functions describe scrape-http --region=us-central1 --format='value(httpsTrigger.url)'
```

#### Test the Cloud Function Scraper
Manually trigger the scraper to populate Firestore:
```bash
# Replace FUNCTION_URL with the URL from above
curl -X POST https://us-central1-$PROJECT_ID.cloudfunctions.net/scrape-http

# Or use gcloud to invoke it
gcloud functions call scrape-http --region=us-central1
```

Check the function logs to see if it ran successfully:
```bash
gcloud functions logs read scrape-http --region=us-central1 --limit=50
```

#### Test the Cloud Run Web App
1. **Get the service URL** (from step above or Cloud Console)
2. **Visit the homepage** in your browser: `https://your-service-url.run.app`
3. **Test the API endpoint**:
   ```bash
   curl https://your-service-url.run.app/api/events
   ```
4. **Check if events are loading**: The page should display events if the scraper has run and populated Firestore.

#### Verify Firestore Data
```bash
# List events in Firestore (requires gcloud CLI)
gcloud firestore export gs://$PROJECT_ID-backup/events-export

# Or use the Cloud Console:
# Navigate to Firestore → Data → events collection
```

#### Common Issues and Debugging

**No events showing on the website:**
1. Check if the scraper has run: `gcloud functions logs read scrape-http --region=us-central1`
2. Verify Firestore has data: Check the Firestore console in Cloud Console
3. Check Cloud Run logs: `gcloud run services logs read aiplusbio-web --region=us-central1`
4. Ensure `USE_FIRESTORE=true` is set on both Cloud Run and Cloud Functions

**Scraper not running:**
1. Check Cloud Scheduler job status: `gcloud scheduler jobs describe scrape-events --location=us-central1`
2. Manually trigger the function to test: `gcloud functions call scrape-http --region=us-central1`
3. Review function logs for errors: `gcloud functions logs read scrape-http --region=us-central1 --limit=100`

**Permission errors:**
1. Ensure service accounts have required roles:
   ```bash
   # Cloud Function needs Firestore access
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
     --role="roles/datastore.user"
   
   # Cloud Run needs Firestore access
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

#### Local Testing with Firestore Emulator (Optional)
For local development that matches the Cloud environment:
```bash
# Install Firestore emulator
gcloud components install cloud-firestore-emulator

# Start emulator
gcloud emulators firestore start

# Set environment variable to use emulator
export FIRESTORE_EMULATOR_HOST=localhost:8080
export USE_FIRESTORE=true
export GOOGLE_CLOUD_PROJECT=your-project-id

# Run your app locally
python app.py
```
