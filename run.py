#!/usr/bin/env python3
"""
AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area - Startup Script
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
        
        print("🚀 Starting AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area...")
        print("📊 Web interface will be available at: http://localhost:5001")
        print("🔄 Background scraping will start automatically")
        print("⏹️  Press Ctrl+C to stop the application")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5001)
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("💡 Make sure you have installed all dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1) 