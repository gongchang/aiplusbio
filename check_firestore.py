#!/usr/bin/env python3
"""Quick script to check if events exist in Firestore."""

import os
import sys

# Set project if not already set
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
if not project_id:
    print("Error: GOOGLE_CLOUD_PROJECT environment variable not set")
    print("Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id")
    sys.exit(1)

try:
    from google.cloud import firestore
    
    client = firestore.Client(project=project_id)
    events_ref = client.collection('events')
    
    # Count documents
    docs = list(events_ref.limit(1).stream())
    if not docs:
        print("❌ No events found in Firestore collection 'events'")
        print("   The collection might be empty or not exist yet.")
        sys.exit(1)
    
    # Get total count (this might be slow for large collections)
    print("📊 Checking Firestore events collection...")
    
    # Get a sample of events
    sample_docs = list(events_ref.limit(10).stream())
    print(f"✅ Found at least {len(sample_docs)} event(s) in Firestore")
    
    if sample_docs:
        print("\n📋 Sample events:")
        for i, doc in enumerate(sample_docs[:5], 1):
            data = doc.to_dict()
            title = data.get('title', 'Untitled')
            date = data.get('date', 'No date')
            print(f"  {i}. {title} ({date})")
        
        # Try to get approximate count (this queries all docs, might be slow)
        print("\n🔢 Counting total events (this may take a moment)...")
        all_docs = list(events_ref.stream())
        print(f"📈 Total events in Firestore: {len(all_docs)}")
    
except ImportError:
    print("Error: google-cloud-firestore not installed")
    print("Install it with: pip install google-cloud-firestore")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error checking Firestore: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure GOOGLE_CLOUD_PROJECT is set correctly")
    print("2. Ensure you're authenticated: gcloud auth application-default login")
    print("3. Check that Firestore is enabled in your project")
    sys.exit(1)

