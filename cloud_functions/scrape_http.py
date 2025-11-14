from __future__ import annotations

import os
from typing import Iterable, Dict

from event_scraper import EventScraper
from event_categorizer import EventCategorizer
from database import Database

USE_FIRESTORE = os.getenv('USE_FIRESTORE', 'true').lower() == 'true'
SQLITE_PATH = os.getenv('DATABASE_PATH', '/tmp/events.db')

if USE_FIRESTORE:
    from firestoreservice import EventStore


def _prepare(events: Iterable[Dict], categorizer: EventCategorizer, db: Database):
    prepared = []
    for event in events:
        event['categories'] = categorizer.categorize_event(event)
        source_url = event.get('source_url') or event.get('url') or ''
        event['source_url'] = source_url
        event['url'] = event.get('url') or source_url
        event['institution'] = event.get('institution') or db.get_institution_from_url(source_url)
        prepared.append(dict(event))
    return prepared


def scrape_http(request):  # Cloud Function HTTP trigger
    db = Database(db_path=SQLITE_PATH)
    scraper = EventScraper(db)
    categorizer = EventCategorizer()

    new_events = scraper.scrape_all_sites()
    prepared_events = _prepare(new_events, categorizer, db)

    if USE_FIRESTORE:
        store = EventStore()
        store.upsert_events(prepared_events)
        store.prune_older_than(days=90)

    return (f"Processed {len(prepared_events)} events", 200)
