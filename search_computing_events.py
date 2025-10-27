#!/usr/bin/env python3
"""
Command line interface for searching computing events using Tavily API.
This script can be run manually to search for new computing events.
"""

import os
import sys
import argparse
from datetime import datetime
from computing_event_searcher import ComputingEventSearcher
from dotenv import load_dotenv


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Search for computing events in Boston area')
    parser.add_argument('--max-results', type=int, default=20, 
                       help='Maximum number of events to search for (default: 20)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Search but do not save to database')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check if Tavily API key is available
    if not os.getenv('Tavily_API'):
        print("Error: TAVILY_API environment variable not set")
        print("Please add your Tavily API key to the .env file:")
        print("TAVILY_API=your_api_key_here")
        sys.exit(1)
    
    print(f"🔍 Searching for computing events in Boston area...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Max results: {args.max_results}")
    print(f"💾 Save to database: {'No' if args.dry_run else 'Yes'}")
    print("-" * 50)
    
    try:
        # Initialize searcher
        searcher = ComputingEventSearcher()
        
        # Search for events
        if args.verbose:
            print("🔍 Building search query...")
        
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
        
        for event in events:
            host = event.get('host', 'Other')
            cost_type = event.get('cost_type', 'Unknown')
            event_categories = event.get('categories', [])
            
            hosts[host] = hosts.get(host, 0) + 1
            cost_types[cost_type] = cost_types.get(cost_type, 0) + 1
            
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
        
        # Display sample events
        print(f"\n📋 Sample Events:")
        print("-" * 30)
        for i, event in enumerate(events[:5], 1):
            print(f"{i}. {event['title']}")
            print(f"   Host: {event.get('host', 'Other')}")
            print(f"   Cost: {event.get('cost_type', 'Unknown')}")
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
        
        print("\n✅ Search completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during search: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
