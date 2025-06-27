#!/usr/bin/env python3
"""
Simple server starter for web interface.
"""

import os
import sys

# Set working directory to web_interface
web_interface_dir = os.path.join(os.path.dirname(__file__), 'web_interface')
os.chdir(web_interface_dir)

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, web_interface_dir)

# Import and run
from app import app, socketio

if __name__ == '__main__':
    print("🕷️  Web Scraper Interface Starting...")
    print("📍 Access the interface at: http://localhost:8080")
    print("🔧 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Run without debug mode to avoid reloader issues
        socketio.run(app, debug=False, host='127.0.0.1', port=8080, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n👋 Web Scraper Interface stopped.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")