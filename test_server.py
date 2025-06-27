#!/usr/bin/env python3
"""
Minimal test server to diagnose connection issues.
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Test Server Working!</h1><p>If you can see this, the server is running correctly.</p>'

if __name__ == '__main__':
    print("🧪 Starting test server...")
    print("📍 Visit: http://localhost:8080")
    print("🔧 Press Ctrl+C to stop")
    
    try:
        app.run(host='127.0.0.1', port=8080, debug=False)
    except Exception as e:
        print(f"❌ Error: {e}")