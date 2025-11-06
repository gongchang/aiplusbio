#!/usr/bin/env python3
"""
Enhanced command line interface for searching computing events using multiple APIs.
This script uses Tavily, Eventbrite, and Luma APIs for comprehensive event discovery.
"""

import os
import sys
import argparse
from datetime import datetime
from enhanced_computing_event_searcher import EnhancedComputingEventSearcher
from dotenv import load_dotenv


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Enhanced search for computing events in Boston area using multiple APIs')
    parser.add_argument('--max-results', type=int, default=20, 
                       help='Maximum number of events to search for (default: 20)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Search but do not save to database')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('--clear-db', action='store_true',
                       help='Clear existing computing events from database before search')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check if required API keys are available
    missing_keys = []
    if not os.getenv('Tavily_API'):
        missing_keys.append('TAVILY_API')
    if not os.getenv('EVENTBRITE_API_KEY'):
        missing_keys.append('EVENTBRITE_API_KEY')
    if not os.getenv('LUMA_API_KEY'):
        missing_keys.append('LUMA_API_KEY')
    
    if missing_keys:
        print("⚠️  Missing API keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nThe search will continue with available APIs only.")
        print("To get API keys:")
        print("  - Tavily: https://tavily.com")
        print("  - Eventbrite: https://www.eventbrite.com/platform/api-keys/")
        print("  - Luma: https://lu.ma/settings/api")
        print()
    
    if args.clear_db:
        print("🗑️  Clearing existing computing events from database...")
        searcher = EnhancedComputingEventSearcher()
        try:
            import sqlite3
            conn = sqlite3.connect(searcher.db.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM computing_events')
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            print(f"✅ Cleared {deleted_count} events from database")
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            return
    
    print(f"🚀 Enhanced search for computing events in Boston area...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Max results: {args.max_results}")
    print(f"💾 Save to database: {'No' if args.dry_run else 'Yes'}")
    print(f"📊 Using APIs: Tavily{'✅' if os.getenv('Tavily_API') else '❌'}, Eventbrite{'✅' if os.getenv('EVENTBRITE_API_KEY') else '❌'}, Luma{'✅' if os.getenv('LUMA_API_KEY') else '❌'}")
    print("-" * 60)
    
    try:
        # Initialize enhanced searcher
        searcher = EnhancedComputingEventSearcher()
        
        # Search for events using multiple APIs
        events = searcher.search_events(max_results=args.max_results)
        
        print(f"✅ Found {len(events)} events")
        
        if not events:
            print("ℹ️  No events found matching the criteria")
            return
        
        # Display events summary
        print("\n📊 Event Summary:")
        print("-" * 30)
        
        hosts = {}
        cost_types = {}
        categories = {}
        sources = {}
        
        for event in events:
            host = event.get('host', 'Other')
            cost_type = event.get('cost_type', 'Unknown')
            event_categories = event.get('categories', [])
            source = event.get('source', 'Unknown')
            
            hosts[host] = hosts.get(host, 0) + 1
            cost_types[cost_type] = cost_types.get(cost_type, 0) + 1
            sources[source] = sources.get(source, 0) + 1
            
            for category in event_categories:
                categories[category] = categories.get(category, 0) + 1
        
        print(f"\n🏢 Events by Host:")
        for host, count in sorted(hosts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {host}: {count}")
        
        print(f"\n💰 Events by Cost Type:")
        for cost_type, count in sorted(cost_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cost_type}: {count}")
        
        print(f"\n🏷️  Events by Category:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        print(f"\n📡 Events by Source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
        
        # Display sample events
        print(f"\n📋 Sample Events:")
        print("-" * 30)
        for i, event in enumerate(events[:5], 1):
            print(f"{i}. {event['title']}")
            print(f"   Host: {event.get('host', 'Other')}")
            print(f"   Cost: {event.get('cost_type', 'Unknown')}")
            print(f"   Source: {event.get('source', 'Unknown')}")
            print(f"   Date: {event.get('date', 'TBD')}")
            print(f"   URL: {event['url']}")
            print()
        
        if len(events) > 5:
            print(f"... and {len(events) - 5} more events")
        
        # Save to database if not dry run
        if not args.dry_run:
            print("\n💾 Saving events to database...")
            saved_count = searcher.save_events_to_database(events)
            print(f"✅ Successfully saved {saved_count} events to database")
            
            # Display database stats
            stats = searcher.db.get_computing_event_stats()
            print(f"\n📈 Database Statistics:")
            print(f"  Total events: {stats['total_events']}")
            print(f"  Events today: {stats['today_events']}")
            print(f"  Events this week: {stats['week_events']}")
        else:
            print("\n🔍 Dry run completed - no events saved to database")
        
        print("\n✅ Enhanced search completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during search: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()




