#!/usr/bin/env python3
"""
Quick Start Script - Load existing data without background scraping
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        from app import app
        from database import Database
        
        # Initialize database (load existing data)
        db = Database()
        db.init_db()
        
        # Get event count
        events = db.get_events()
        print(f"📊 Loaded {len(events)} existing events from database")
        
        print("🚀 Starting AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area (Quick Start)...")
        print("📊 Web interface will be available at: http://localhost:5001")
        print("⚠️  Background scraping is DISABLED - using existing data only")
        print("⏹️  Press Ctrl+C to stop the application")
        print("-" * 50)
        
        # Start Flask app without background scraping
        app.run(debug=True, host='0.0.0.0', port=5001)
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("💡 Make sure you have installed all dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1) 