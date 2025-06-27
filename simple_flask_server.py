#!/usr/bin/env python3
"""
Simple Flask server without Socket.IO dependencies.
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
import zipfile
import tempfile

# Add parent directory to path to import webscraper modules
sys.path.insert(0, os.path.dirname(__file__))
web_interface_dir = os.path.join(os.path.dirname(__file__), 'web_interface')
sys.path.insert(0, web_interface_dir)

from webscraper_src.config import Config
from webscraper_src.scraper import WebScraper
from webscraper_src.utils import get_domain, is_valid_url

# Initialize Flask app
app = Flask(__name__, 
           template_folder=os.path.join(web_interface_dir, 'templates'),
           static_folder=os.path.join(web_interface_dir, 'static'))

app.config['SECRET_KEY'] = 'webscraper-secret-key-change-in-production'

# Global state management
active_jobs: Dict[str, Dict[str, Any]] = {}
job_history: list = []
job_lock = threading.Lock()

# Load job history from file if it exists
HISTORY_FILE = Path(web_interface_dir) / 'job_history.json'

def load_job_history():
    """Load job history from file."""
    global job_history
    try:
        print(f"Loading job history from: {HISTORY_FILE}")
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                loaded_history = json.load(f)
                job_history = loaded_history
                print(f"Loaded {len(job_history)} jobs from history")
        else:
            print("No history file found, starting with empty history")
            job_history = []
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
        'status_message': 'Job created, waiting to start...',
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
    """Update job status."""
    with job_lock:
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = status
            active_jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
            for key, value in kwargs.items():
                if key == 'stats':
                    active_jobs[job_id]['stats'].update(value)
                else:
                    active_jobs[job_id][key] = value
            
            print(f"📊 Job {job_id}: {status} - {active_jobs[job_id].get('progress', 0)}% - {active_jobs[job_id].get('status_message', '')}")

def run_scraping_job(job_id: str, url: str, config_dict: Dict[str, Any]):
    """Run scraping job in background thread."""
    try:
        update_job_status(job_id, 'running', progress=5, status_message="Initializing scraper...")
        
        # Create config object
        config = Config.from_dict(config_dict)
        config.validate()
        
        update_job_status(job_id, 'running', progress=10, status_message="Configuration loaded, starting scraper...")
        
        # Initialize scraper
        with WebScraper(config) as scraper:
            update_job_status(job_id, 'running', progress=15, status_message="Scraper initialized, beginning URL analysis...")
            
            # Get estimated work for progress tracking
            max_depth = config_dict.get('max_depth', 1)
            estimated_pages = min(max_depth * 10, 50)
            urls_processed = 0
            files_downloaded = 0
            
            # Create a custom progress callback
            def progress_callback(current_url: str, depth: int, media_count: int = 0):
                nonlocal urls_processed, files_downloaded
                urls_processed += 1
                files_downloaded += media_count
                
                # Calculate progress (20% for setup, 80% for scraping)
                scraping_progress = min((urls_processed / estimated_pages) * 80, 80)
                total_progress = 20 + scraping_progress
                
                # Create descriptive status message
                domain = get_domain(current_url)
                status_message = f"Scraping {domain} (depth {depth}) - {media_count} media files found"
                
                update_job_status(job_id, 'running', 
                                progress=min(total_progress, 95),
                                status_message=status_message,
                                stats={
                                    'urls_processed': urls_processed,
                                    'files_downloaded': files_downloaded,
                                    'total_size': files_downloaded * 50000,  # Estimate
                                    'errors': 0
                                })
            
            # Patch the scraper to call our progress callback
            original_scrape_url = scraper.scrape_url
            def scrape_url_with_progress(url_to_scrape: str, depth: int = 0):
                result = original_scrape_url(url_to_scrape, depth)
                if result['success']:
                    media_count = len(result['media_urls']['images']) + len(result['media_urls']['videos'])
                    progress_callback(url_to_scrape, depth, media_count)
                return result
            
            scraper.scrape_url = scrape_url_with_progress
            
            # Run scraping
            results = scraper.scrape_and_download(url)
            
            # Update to final progress before completion
            update_job_status(job_id, 'running', progress=98, status_message="Finalizing results...")
            time.sleep(0.5)  # Brief pause to ensure frontend sees this update
            
            # Process final results
            stats = results.get('stats', {})
            download_stats = stats.get('download_stats', {})
            
            final_stats = {
                'urls_processed': stats.get('total_urls_scraped', 0),
                'files_downloaded': download_stats.get('successful_downloads', 0),
                'total_size': download_stats.get('total_bytes', 0),
                'errors': download_stats.get('failed_downloads', 0)
            }
            
            # Complete job with 100% progress
            completion_message = f"Scraping completed! {final_stats['urls_processed']} pages, {final_stats['files_downloaded']} files downloaded"
            update_job_status(job_id, 'completed', 
                            progress=100,
                            status_message=completion_message,
                            stats=final_stats,
                            results=results)
            
            print(f"✅ Job {job_id} marked as completed with 100% progress")
            
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
        print(f"Scraping job {job_id} failed: {error_msg}")
        update_job_status(job_id, 'failed', 
                         error_message=error_msg,
                         status_message=f"Error: {error_msg[:100]}...")
        
        # Add failed job to history
        job_record = active_jobs[job_id].copy()
        with job_lock:
            job_history.insert(0, job_record)
        save_job_history()
    
    finally:
        # Remove from active jobs after delay
        def cleanup_job():
            time.sleep(60)  # Keep for 60 seconds for client to get final status
            with job_lock:
                if job_id in active_jobs:
                    print(f"🧹 Cleaning up job {job_id} from active jobs")
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

# Initialize
load_job_history()

if __name__ == '__main__':
    print("🕷️  Simple Web Scraper Interface Starting...")
    print("📍 Access the interface at: http://localhost:8080")
    print("🔧 Press Ctrl+C to stop the server")
    print("✅ No Socket.IO - using simple polling for updates")
    
    try:
        app.run(host='127.0.0.1', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 Web Scraper Interface stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")