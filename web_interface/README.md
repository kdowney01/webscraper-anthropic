# Web Scraper Interface

A modern web interface for the webscraper project built with Flask and Socket.IO.

## Features

✅ **Real-time scraping** with WebSocket progress updates
✅ **Interactive form** with validation and configuration options
✅ **Job management** with history and re-run capabilities
✅ **Progress tracking** with live statistics
✅ **File downloads** as ZIP archives
✅ **Responsive design** that works on mobile and desktop

## Quick Start

### 1. Install Dependencies
```bash
# From the webscraper root directory
python3 -m pip install --user flask flask-socketio
```

### 2. Run the Interface
```bash
# Option 1: Using the convenience script
python3 run_web_interface.py

# Option 2: Direct Flask app
cd web_interface
python3 app.py
```

### 3. Open Browser
Visit: **http://localhost:8080**

## Architecture

### Backend (Flask + Socket.IO)
- **`app.py`** - Main Flask application with API endpoints
- **Real-time updates** via WebSocket for job progress
- **Background processing** with threading for scraping jobs
- **Job persistence** with JSON file storage
- **API endpoints** for all scraping operations

### Frontend (HTML + CSS + JavaScript)
- **`templates/index.html`** - Main interface template
- **`static/css/style.css`** - Professional styling and responsive design
- **`static/js/app.js`** - Interactive JavaScript with WebSocket client
- **Real-time UI updates** and form validation

### Key Components

#### API Endpoints
- `POST /api/scrape` - Start new scraping job
- `POST /api/dry-run` - Preview what would be scraped
- `GET /api/status/<job_id>` - Get job status
- `GET /api/jobs` - List active jobs and history
- `POST /api/jobs/<job_id>/cancel` - Cancel running job
- `GET /api/jobs/<job_id>/download` - Download results as ZIP
- `POST /api/history/clear` - Clear job history

#### WebSocket Events
- `connect/disconnect` - Client connection management
- `job_update` - Real-time progress updates
- `subscribe_job` - Subscribe to specific job updates

#### Core Features
- **Form validation** with real-time URL checking
- **Progress tracking** with animated progress bars
- **Job history** with re-run functionality
- **File downloads** with ZIP packaging
- **Error handling** with user-friendly notifications

## Configuration Options

The interface supports all webscraper configuration options:

### Basic Settings
- **URL** - Target website to scrape
- **Max Depth** - How deep to follow links (1-5)
- **Ignore Robots.txt** - Override robots.txt restrictions
- **Content Types** - Choose images, videos, text

### Advanced Settings
- **Max Workers** - Concurrent download threads (1-10)
- **Delay** - Time between requests (0.5-5.0 seconds)
- **User Agent** - Custom user agent string

## File Structure

```
web_interface/
├── app.py                 # Flask application
├── templates/
│   └── index.html        # Main interface template
├── static/
│   ├── css/
│   │   └── style.css     # Interface styling
│   └── js/
│       └── app.js        # Frontend JavaScript
├── job_history.json      # Job history storage (auto-created)
└── README.md            # This file
```

## Development

### Adding New Features

1. **Backend API**: Add new routes in `app.py`
2. **Frontend UI**: Update `templates/index.html`
3. **Styling**: Modify `static/css/style.css`
4. **JavaScript**: Add functionality in `static/js/app.js`

### WebSocket Communication

The interface uses Socket.IO for real-time updates:

```javascript
// Client subscribes to job updates
socket.emit('subscribe_job', { job_id: 'job-uuid' });

// Server sends progress updates
socket.emit('job_update', {
    job_id: 'job-uuid',
    status: 'running',
    data: { progress: 75, stats: {...} }
});
```

### Job Management

Jobs flow through these states:
1. **pending** - Job created, not started
2. **running** - Actively scraping
3. **completed** - Successfully finished
4. **failed** - Error occurred
5. **cancelled** - User cancelled

## Integration with CLI

The web interface integrates seamlessly with the existing CLI:
- Uses the same `webscraper_src` modules
- Applies same configuration options
- Produces identical results
- Saves to same directory structure

## Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
- Ensure you're in the correct directory
- Install dependencies: `pip install flask flask-socketio`

**"Port already in use"**
- Change port in `app.py`: `socketio.run(app, port=5001)`
- Or kill existing process: `lsof -ti:5000 | xargs kill`

**"Permission denied"**
- Check file permissions for downloads directory
- Ensure write access to web_interface directory

### Debug Mode

The interface runs in debug mode by default with:
- **Auto-reload** on code changes
- **Detailed error messages** in browser
- **Console logging** for troubleshooting

## Security Notes

⚠️ **Important**: This interface is designed for local development use.

For production deployment:
- Change the Flask secret key
- Add authentication/authorization
- Configure CORS properly
- Use a production WSGI server
- Implement rate limiting
- Validate all inputs server-side

## Performance

The interface is optimized for:
- **Concurrent jobs** - Multiple scraping jobs can run simultaneously
- **Large files** - Streaming downloads for large ZIP files
- **Real-time updates** - Efficient WebSocket communication
- **Responsive UI** - Fast form validation and updates

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires JavaScript enabled for full functionality.