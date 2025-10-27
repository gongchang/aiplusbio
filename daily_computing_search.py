#!/usr/bin/env python3
"""
Daily automated search for computing events.
This script is designed to be run at the end of each day via cron job.
"""

import os
import sys
import logging
from datetime import datetime
from computing_event_searcher import ComputingEventSearcher
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('computing_events_search.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Daily search for computing events"""
    logger.info("Starting daily computing events search")
    
    # Load environment variables
    load_dotenv()
    
    # Check if Tavily API key is available
    if not os.getenv('Tavily_API'):
        logger.error("TAVILY_API environment variable not set")
        sys.exit(1)
    
    try:
        # Initialize searcher
        searcher = ComputingEventSearcher()
        
        # Search for events
        logger.info("Searching for computing events...")
        events = searcher.search_events(max_results=20)  # Search for top 20 events daily
        
        if not events:
            logger.info("No new events found")
            return
        
        logger.info(f"Found {len(events)} events")
        
        # Save events to database
        saved_count = searcher.save_events_to_database(events)
        logger.info(f"Saved {saved_count} new events to database")
        
        # Log summary statistics
        stats = searcher.db.get_computing_event_stats()
        logger.info(f"Database now contains {stats['total_events']} total events")
        
        # Log breakdown by cost type and host
        if stats['cost_type_stats']:
            logger.info("Events by cost type:")
            for cost_type, count in stats['cost_type_stats'].items():
                logger.info(f"  {cost_type}: {count}")
        
        if stats['host_stats']:
            logger.info("Top hosts:")
            for host, count in list(stats['host_stats'].items())[:5]:
                logger.info(f"  {host}: {count}")
        
        logger.info("Daily computing events search completed successfully")
        
    except Exception as e:
        logger.error(f"Error during daily search: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
