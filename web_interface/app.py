"""
Flask web application for the webscraper interface.
"""

import os
import sys
import json
import uuid
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, disconnect
import zipfile
import tempfile

# Add parent directory to path to import webscraper modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webscraper_src.config import Config
from webscraper_src.scraper import WebScraper
from webscraper_src.utils import get_domain, is_valid_url

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'webscraper-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state management
active_jobs: Dict[str, Dict[str, Any]] = {}
job_history: list = []
job_lock = threading.Lock()

# Load job history from file if it exists
HISTORY_FILE = Path(__file__).parent / 'job_history.json'

def load_job_history():
    """Load job history from file."""
    global job_history
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                job_history = json.load(f)
    except Exception as e:
        print(f"Error loading job history: {e}")
        job_history = []

def save_job_history():
    """Save job history to file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(job_history[-50:], f, indent=2)  # Keep last 50 jobs
    except Exception as e:
        print(f"Error saving job history: {e}")

def create_job_record(job_id: str, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new job record."""
    return {
        'id': job_id,
        'url': url,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'config': config,
        'progress': 0,
        'stats': {
            'urls_processed': 0,
            'files_downloaded': 0,
            'total_size': 0,
            'errors': 0
        },
        'results': None,
        'error_message': None
    }

def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status and emit to client."""
    with job_lock:
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = status
            active_jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
            for key, value in kwargs.items():
                if key == 'stats':
                    active_jobs[job_id]['stats'].update(value)
                else:
                    active_jobs[job_id][key] = value
            
            # Emit update to client
            socketio.emit('job_update', {
                'job_id': job_id,
                'status': status,
                'data': active_jobs[job_id]
            })

def run_scraping_job(job_id: str, url: str, config_dict: Dict[str, Any]):
    """Run scraping job in background thread."""
    try:
        update_job_status(job_id, 'running', progress=0)
        
        # Create config object
        config = Config.from_dict(config_dict)
        config.validate()
        
        # Initialize scraper
        with WebScraper(config) as scraper:
            # Mock progress updates for demonstration
            update_job_status(job_id, 'running', progress=10)
            time.sleep(0.5)
            
            # Run scraping
            results = scraper.scrape_and_download(url)
            
            # Update progress
            update_job_status(job_id, 'running', progress=100)
            
            # Process results
            stats = results.get('stats', {})
            download_stats = stats.get('download_stats', {})
            
            final_stats = {
                'urls_processed': stats.get('total_urls_scraped', 0),
                'files_downloaded': download_stats.get('successful_downloads', 0),
                'total_size': download_stats.get('total_bytes', 0),
                'errors': download_stats.get('failed_downloads', 0)
            }
            
            # Complete job
            update_job_status(job_id, 'completed', 
                            progress=100, 
                            stats=final_stats,
                            results=results)
            
            # Add to history
            job_record = active_jobs[job_id].copy()
            job_record['duration'] = time.time() - time.mktime(
                datetime.fromisoformat(job_record['created_at']).timetuple()
            )
            
            with job_lock:
                job_history.insert(0, job_record)
                if len(job_history) > 50:
                    job_history.pop()
            
            save_job_history()
            
    except Exception as e:
        error_msg = str(e)
        update_job_status(job_id, 'failed', error_message=error_msg)
        
        # Add failed job to history
        job_record = active_jobs[job_id].copy()
        with job_lock:
            job_history.insert(0, job_record)
        save_job_history()
    
    finally:
        # Remove from active jobs after delay
        def cleanup_job():
            time.sleep(30)  # Keep for 30 seconds for client to get final status
            with job_lock:
                if job_id in active_jobs:
                    del active_jobs[job_id]
        
        threading.Thread(target=cleanup_job, daemon=True).start()

# Routes

@app.route('/')
def index():
    """Main interface page."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    config = Config()
    return jsonify(config.to_dict())

@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start a new scraping job."""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        if not is_valid_url(url):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Extract configuration
        config_dict = {
            'max_depth': data.get('max_depth', 1),
            'respect_robots_txt': not data.get('ignore_robots', False),
            'download_images': data.get('download_images', True),
            'download_videos': data.get('download_videos', True),
            'download_text': data.get('download_text', True),
            'max_workers': data.get('max_workers', 5),
            'delay_between_requests': data.get('delay', 1.0),
            'user_agent': data.get('user_agent', 'WebScraper/1.0')
        }
        
        # Create job record
        job_record = create_job_record(job_id, url, config_dict)
        
        with job_lock:
            active_jobs[job_id] = job_record
        
        # Start scraping in background thread
        thread = threading.Thread(
            target=run_scraping_job,
            args=(job_id, url, config_dict),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Scraping job started successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dry-run', methods=['POST'])
def dry_run():
    """Perform a dry run analysis."""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        if not is_valid_url(url):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Mock dry run results
        domain = get_domain(url)
        max_depth = data.get('max_depth', 1)
        
        # Simulate what would be scraped
        estimated_pages = min(max_depth * 10, 50)  # Rough estimate
        estimated_images = estimated_pages * 5 if data.get('download_images', True) else 0
        estimated_videos = estimated_pages * 2 if data.get('download_videos', True) else 0
        
        results = {
            'url': url,
            'domain': domain,
            'max_depth': max_depth,
            'respect_robots': not data.get('ignore_robots', False),
            'estimated_pages': estimated_pages,
            'estimated_images': estimated_images,
            'estimated_videos': estimated_videos,
            'estimated_total_files': estimated_pages + estimated_images + estimated_videos,
            'config': data
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status."""
    with job_lock:
        if job_id in active_jobs:
            return jsonify(active_jobs[job_id])
        else:
            # Check history
            for job in job_history:
                if job['id'] == job_id:
                    return jsonify(job)
            
            return jsonify({'error': 'Job not found'}), 404

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all active jobs and recent history."""
    with job_lock:
        return jsonify({
            'active_jobs': list(active_jobs.values()),
            'history': job_history[:20]  # Last 20 jobs
        })

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel an active job."""
    with job_lock:
        if job_id in active_jobs:
            update_job_status(job_id, 'cancelled')
            return jsonify({'message': 'Job cancelled successfully'})
        else:
            return jsonify({'error': 'Job not found or not active'}), 404

@app.route('/api/jobs/<job_id>/download', methods=['GET'])
def download_job_results(job_id):
    """Download job results as ZIP file."""
    try:
        # Find job
        job = None
        with job_lock:
            if job_id in active_jobs:
                job = active_jobs[job_id]
            else:
                for h_job in job_history:
                    if h_job['id'] == job_id:
                        job = h_job
                        break
        
        if not job or job['status'] != 'completed':
            return jsonify({'error': 'Job not found or not completed'}), 404
        
        # Create temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        try:
            with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
                # Add job info
                job_info = {
                    'job_id': job_id,
                    'url': job['url'],
                    'completed_at': job['updated_at'],
                    'stats': job['stats']
                }
                zipf.writestr('job_info.json', json.dumps(job_info, indent=2))
                
                # Add downloaded files (this would be the actual implementation)
                # For now, add a placeholder
                zipf.writestr('README.txt', 
                    f"Scraping results for: {job['url']}\n"
                    f"Completed: {job['updated_at']}\n"
                    f"Files downloaded: {job['stats']['files_downloaded']}\n"
                    f"URLs processed: {job['stats']['urls_processed']}")
            
            return send_file(
                temp_zip.name,
                as_attachment=True,
                download_name=f"scrape_results_{job_id[:8]}.zip",
                mimetype='application/zip'
            )
            
        finally:
            # Clean up temp file after a delay
            def cleanup():
                time.sleep(60)
                try:
                    os.unlink(temp_zip.name)
                except:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear job history."""
    try:
        with job_lock:
            job_history.clear()
        
        save_job_history()
        
        return jsonify({'message': 'History cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('connected', {'message': 'Connected to webscraper server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('subscribe_job')
def handle_subscribe_job(data):
    """Subscribe to job updates."""
    job_id = data.get('job_id')
    if job_id:
        # Send current status if job exists
        with job_lock:
            if job_id in active_jobs:
                emit('job_update', {
                    'job_id': job_id,
                    'status': active_jobs[job_id]['status'],
                    'data': active_jobs[job_id]
                })

# Initialize
load_job_history()

if __name__ == '__main__':
    # Run the Flask-SocketIO app
    print("Starting Web Scraper Interface...")
    print("Access the interface at: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)