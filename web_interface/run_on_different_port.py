#!/usr/bin/env python3
"""
Alternative port runner for the web interface.
Use this if you have port conflicts.
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, socketio

def main():
    parser = argparse.ArgumentParser(description='Run Web Scraper Interface on custom port')
    parser.add_argument('--port', '-p', type=int, default=8080, 
                       help='Port to run the server on (default: 8080)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    
    args = parser.parse_args()
    
    print(f"🕷️  Web Scraper Interface Starting...")
    print(f"📍 Access the interface at: http://{args.host}:{args.port}")
    print(f"🔧 Press Ctrl+C to stop the server")
    print()
    
    try:
        socketio.run(app, debug=True, host=args.host, port=args.port, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n👋 Web Scraper Interface stopped.")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {args.port} is already in use.")
            print(f"💡 Try a different port: python3 run_on_different_port.py --port {args.port + 1}")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()