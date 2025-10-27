#!/usr/bin/env python3
"""
Analyze website scraping performance
"""

import sqlite3

def analyze_websites():
    """Analyze all websites and their scraping performance"""
    
    print("🔍 Website Scraping Analysis")
    print("=" * 60)
    
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Get all monitored websites
    with open('websites_to_watch.txt', 'r') as f:
        monitored_sites = [line.strip() for line in f if line.strip()]
    
    print(f"📊 Total monitored websites: {len(monitored_sites)}")
    print()
    
    # Get event counts for each website
    cursor.execute('''
        SELECT source_url, COUNT(*) as event_count 
        FROM events 
        WHERE date >= date('now') 
        GROUP BY source_url 
        ORDER BY event_count DESC
    ''')
    
    event_counts = dict(cursor.fetchall())
    
    # Get recent scraping logs
    cursor.execute('''
        SELECT source_url, status, events_found, error_message 
        FROM scraping_log 
        WHERE scraped_at >= datetime('now', '-1 day')
        ORDER BY scraped_at DESC
    ''')
    
    scraping_results = {}
    for row in cursor.fetchall():
        url, status, events_found, error = row
        if url not in scraping_results:
            scraping_results[url] = {
                'status': status,
                'events_found': events_found,
                'error': error,
                'last_check': 'Recent'
            }
    
    # Analyze each website
    print("🌐 Website Performance Analysis:")
    print("-" * 60)
    
    total_events = 0
    working_sites = 0
    problematic_sites = 0
    
    for i, site in enumerate(monitored_sites, 1):
        event_count = event_counts.get(site, 0)
        total_events += event_count
        
        scraping_info = scraping_results.get(site, {})
        status = scraping_info.get('status', 'Unknown')
        events_found = scraping_info.get('events_found', 0)
        error = scraping_info.get('error', '')
        
        # Determine status
        if event_count > 0:
            status_icon = "✅"
            working_sites += 1
            status_desc = f"Working ({event_count} events)"
        elif status == 'success' and events_found == 0:
            status_icon = "⚠️"
            status_desc = "Working but no events found"
        elif status == 'error' or error:
            status_icon = "❌"
            problematic_sites += 1
            status_desc = f"Error: {error[:50]}..."
        else:
            status_icon = "❓"
            status_desc = "Unknown status"
        
        print(f"{i:2d}. {status_icon} {site}")
        print(f"    └─ {status_desc}")
        print()
    
    # Summary
    print("📈 Summary:")
    print("-" * 60)
    print(f"✅ Working websites: {working_sites}/{len(monitored_sites)}")
    print(f"❌ Problematic websites: {problematic_sites}/{len(monitored_sites)}")
    print(f"📊 Total events found: {total_events}")
    print(f"📅 Date range: Events from today onwards")
    
    # Identify potential issues
    print("\n🔍 Potential Issues Identified:")
    print("-" * 60)
    
    sites_with_no_events = [site for site in monitored_sites if event_counts.get(site, 0) == 0]
    
    if sites_with_no_events:
        print("❌ Sites with 0 events (potential scraping issues):")
        for site in sites_with_no_events:
            print(f"   • {site}")
    else:
        print("✅ All sites have events - no obvious scraping issues")
    
    # Sites with many events (working well)
    high_event_sites = [(site, count) for site, count in event_counts.items() if count > 10]
    if high_event_sites:
        print("\n✅ Sites working well (10+ events):")
        for site, count in high_event_sites:
            print(f"   • {site} ({count} events)")
    
    conn.close()

if __name__ == '__main__':
    analyze_websites()
