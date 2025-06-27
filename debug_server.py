#!/usr/bin/env python3
"""
Debug version of the web interface to isolate issues.
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, jsonify

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
web_interface_dir = os.path.join(os.path.dirname(__file__), 'web_interface')
sys.path.insert(0, web_interface_dir)

app = Flask(__name__, 
           template_folder=os.path.join(web_interface_dir, 'templates'),
           static_folder=os.path.join(web_interface_dir, 'static'))

# Test data
test_history = [
    {
        "id": "test-job-1",
        "url": "https://example.com",
        "status": "completed",
        "created_at": "2025-06-17T19:29:42.205310",
        "updated_at": "2025-06-17T19:29:42.567400",
        "progress": 100,
        "status_message": "Scraping completed! 1 pages, 5 files downloaded",
        "stats": {
            "urls_processed": 1,
            "files_downloaded": 5,
            "total_size": 250000,
            "errors": 0
        }
    },
    {
        "id": "test-job-2", 
        "url": "https://test.com",
        "status": "failed",
        "created_at": "2025-06-17T18:15:30.123456",
        "updated_at": "2025-06-17T18:15:45.654321",
        "progress": 25,
        "status_message": "Error: Connection timeout",
        "stats": {
            "urls_processed": 0,
            "files_downloaded": 0,
            "total_size": 0,
            "errors": 1
        }
    }
]

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f'''
        <h1>Debug Server</h1>
        <p>Template error: {e}</p>
        <p>This is a minimal debug server to test the API endpoints.</p>
        <script>
        // Test API calls
        fetch('/api/jobs')
            .then(r => r.json())
            .then(data => {{
                console.log('API response:', data);
                document.body.innerHTML += '<pre>API Response: ' + JSON.stringify(data, null, 2) + '</pre>';
            }})
            .catch(e => console.error('API error:', e));
        </script>
        '''

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Test endpoint for jobs."""
    return jsonify({
        'active_jobs': [],
        'history': test_history
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Test config endpoint."""
    return jsonify({
        'output_dir': '/Users/kyledowney/projects/webscraper/scraped',
        'max_depth': 1,
        'max_workers': 5,
        'delay_between_requests': 1.0
    })

if __name__ == '__main__':
    print("🧪 Debug Server Starting...")
    print("📍 Visit: http://localhost:8080")
    print("🧩 Testing API endpoints and template rendering")
    
    try:
        app.run(host='127.0.0.1', port=8080, debug=False)
    except Exception as e:
        print(f"❌ Error: {e}")