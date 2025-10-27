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

Create a `.env` file in the project root with the following variables:

```env
# OpenAI API Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_PATH=events.db

# Scraping Configuration
SCRAPING_INTERVAL_HOURS=6
REQUEST_TIMEOUT=30

# Logging Configuration
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