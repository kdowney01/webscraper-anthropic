#!/usr/bin/env python3
"""
Working Flask-SocketIO server with proper configuration.
"""

import os
import sys
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
web_interface_dir = os.path.join(os.path.dirname(__file__), 'web_interface')
sys.path.insert(0, web_interface_dir)

app = Flask(__name__, 
           template_folder=os.path.join(web_interface_dir, 'templates'),
           static_folder=os.path.join(web_interface_dir, 'static'))

app.config['SECRET_KEY'] = 'webscraper-secret-key'

# Initialize SocketIO with eventlet
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   logger=False,
                   engineio_logger=False)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Web Scraper - Working Test</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                .success {{ color: #27ae60; background: #ecf0f1; padding: 20px; border-radius: 5px; }}
                .error {{ color: #e74c3c; background: #fadbd8; padding: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>🕷️ Web Scraper Interface</h1>
            <div class="success">
                ✅ <strong>Socket.IO Server is working!</strong><br>
                Flask-SocketIO server started successfully with eventlet.
            </div>
            <div class="error">
                ⚠️ Template not found: {str(e)}<br>
                But the Socket.IO server is running correctly.
            </div>
            <p>Template path: {os.path.join(web_interface_dir, 'templates')}</p>
        </body>
        </html>
        '''

@socketio.on('connect')
def handle_connect():
    print('Client connected to Socket.IO')
    emit('connected', {'message': 'Successfully connected to Socket.IO server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from Socket.IO')

@socketio.on('test')
def handle_test(data):
    print(f'Received test message: {data}')
    emit('test_response', {'message': 'Socket.IO is working!'})

if __name__ == '__main__':
    print("🕷️  Socket.IO Web Scraper Test")
    print("📍 Visit: http://localhost:8080")
    print("🔧 Press Ctrl+C to stop")
    
    try:
        socketio.run(app, 
                    host='127.0.0.1', 
                    port=8080, 
                    debug=False,
                    use_reloader=False)
    except Exception as e:
        print(f"❌ Error: {e}")