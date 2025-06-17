#!/usr/bin/env python3
"""
Convenient script to run the web interface.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
web_interface_dir = os.path.join(os.path.dirname(__file__), 'web_interface')
sys.path.insert(0, web_interface_dir)

# Change to web_interface directory for relative imports
os.chdir(web_interface_dir)
from app import app, socketio

if __name__ == '__main__':
    print("🕷️  Web Scraper Interface Starting...")
    print("📍 Access the interface at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    print()
    
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Web Scraper Interface stopped.")
        sys.exit(0)