import argparse
from datetime import datetime

from database import Database
from event_scraper import EventScraper


def parse_args():
    parser = argparse.ArgumentParser(
        description="Retroactively enrich stored events with better titles, descriptions, and times."
    )
    parser.add_argument(
        "--days-ahead",
        type=int,
        default=365,
        help="How far into the future to search for events that need enrichment (default: 365)."
    )
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Also inspect past events (within the lookback window)."
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=365,
        help="How many days back to include when --include-past is set (default: 365)."
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Maximum number of events to process (0 means no limit, default: 0)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    db = Database()
    scraper = EventScraper(db)

    max_events = args.max_events if args.max_events > 0 else 0
    updated = scraper.refresh_event_metadata(
        days_ahead=args.days_ahead,
        include_past=args.include_past,
        lookback_days=args.lookback_days,
        max_events=max_events
    )

    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"Enrichment complete. Updated {updated} event(s)."
    )


if __name__ == "__main__":
    main()

