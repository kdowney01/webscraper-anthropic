#!/usr/bin/env python3
"""
Simple Flask server without Socket.IO for testing.
"""

import os
import sys
from flask import Flask, render_template

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
web_interface_dir = os.path.join(os.path.dirname(__file__), 'web_interface')
sys.path.insert(0, web_interface_dir)

app = Flask(__name__, 
           template_folder=os.path.join(web_interface_dir, 'templates'),
           static_folder=os.path.join(web_interface_dir, 'static'))

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Web Scraper - Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #2c3e50; }
            .success { color: #27ae60; background: #ecf0f1; padding: 20px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🕷️ Web Scraper Interface</h1>
        <div class="success">
            ✅ <strong>Server is working!</strong><br>
            If you can see this page, the Flask server is running correctly.
        </div>
        <p>Next step: Test the full interface with Socket.IO</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🕷️  Simple Web Scraper Test")
    print("📍 Visit: http://localhost:8080")
    print("🔧 Press Ctrl+C to stop")
    
    try:
        app.run(host='127.0.0.1', port=8080, debug=False)
    except Exception as e:
        print(f"❌ Error: {e}")