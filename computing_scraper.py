"""Verified free industry/community computing events: Boston in-person or online anywhere."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

SOURCES = (
    ('https://gdg.community.dev/gdg-cloud-boston/', 'GDG Cloud Boston'),
    ('https://gdg.community.dev/gdg-grand-rapids/', 'GDG Grand Rapids'),
)
# Official event pages: only their explicitly free online option is published.
VIRTUAL_EVENTS = (
    ('https://githubuniverse.com/', 'GitHub', 'GitHub Universe',
     r'register virtually for free', r'october\s+28\s*[–-]\s*29', 'October 28'),
    ('https://aws.amazon.com/events/reinvent/livestream/', 'Amazon Web Services', 'AWS re:Invent Livestream',
     r'register for the free livestream', r'nov\.?\s*30\s*[–-]\s*dec\.?\s*4', 'November 30'),
)
ALLOWED_SOURCES = {host for _, host in SOURCES} | {host for _, host, *_ in VIRTUAL_EVENTS}
BOSTON_AREA = ('boston', 'cambridge', 'somerville', 'brookline', 'newton',
               'waltham', 'watertown', 'medford', 'arlington', 'lexington')


def scrape_free_events(session=None):
    session = session or requests.Session()
    events = []
    for source, host in SOURCES:
        response = session.get(source, timeout=12)
        response.raise_for_status()
        listing = BeautifulSoup(response.content, 'html.parser')
        seen = set()
        for link in listing.select('a[href*="/events/details/"]'):
            url = link.get('href', '')
            if url in seen or urlparse(url).hostname != 'gdg.community.dev':
                continue
            seen.add(url)
            # Free admission must be indicated on this card, not elsewhere on the page.
            card = next((p for p in link.parents if p.name in ('div', 'article')
                         and 'free registration' in p.get_text(' ', strip=True).lower()
                         and len(p.get_text(' ', strip=True)) < 650), None)
            if not card or len(seen) > 8:  # ponytail: bounded detail requests; paginate only if coverage demands it.
                continue
            try:
                detail = session.get(url, timeout=12)
                detail.raise_for_status()
                page = BeautifulSoup(detail.content, 'html.parser')
                for script in page.select('script[type="application/ld+json"]'):
                    data = json.loads(script.get_text())
                    for item in data if isinstance(data, list) else [data]:
                        if not isinstance(item, dict) or item.get('@type') != 'Event' or not item.get('name') or not item.get('startDate'):
                            continue
                        start = datetime.fromisoformat(item['startDate'].replace('Z', '+00:00'))
                        if start.date() < datetime.now(timezone.utc).date():
                            continue
                        offers = item.get('offers') or []
                        if isinstance(offers, dict):
                            offers = [offers]
                        if any(float(offer.get('price') or 0) > 0 for offer in offers):
                            continue
                        place = item.get('location') or {}
                        virtual = isinstance(place, dict) and place.get('@type') == 'VirtualLocation'
                        address = place.get('address') or {} if isinstance(place, dict) else {}
                        city = address.get('addressLocality', '') if isinstance(address, dict) else ''
                        location = ('Virtual' if virtual else ', '.join(filter(None, (place.get('name', ''), city)))) if isinstance(place, dict) else str(place)
                        if not virtual and not any(city in location.lower() for city in BOSTON_AREA):
                            continue
                        events.append({
                            'title': item['name'], 'description': item.get('description', ''),
                            'date': start.date().isoformat(), 'time': start.strftime('%I:%M %p'),
                            'location': location, 'url': url, 'source_url': source,
                            'host': 'Google Developer Groups', 'source': host, 'cost_type': 'Free',
                            'categories': ['Technology'], 'is_virtual': virtual,
                            'requires_registration': True,
                        })
            except (requests.RequestException, ValueError, TypeError, KeyError):
                continue  # A removed/malformed event must not hide other valid events.
    for url, host, name, free_phrase, date_phrase, month_day in VIRTUAL_EVENTS:
        try:
            response = session.get(url, timeout=12)
            response.raise_for_status()
            page = BeautifulSoup(response.content, 'html.parser')
            title = page.title.get_text(' ', strip=True) if page.title else ''
            year = re.search(r'\b20\d{2}\b', title)
            text = page.get_text(' ', strip=True)
            if not (year and re.search(free_phrase, text, re.I) and re.search(date_phrase, text, re.I)):
                continue
            event_date = datetime.strptime(f'{month_day} {year.group()}', '%B %d %Y').date()
            if event_date < datetime.now(timezone.utc).date():
                continue
            events.append({
                'title': f'{name} {year.group()} (free virtual access)',
                'description': f'Free virtual access to {name}; in-person admission is not included.',
                'date': event_date.isoformat(), 'time': '', 'location': 'Virtual',
                'url': url, 'source_url': url, 'host': host, 'source': host,
                'cost_type': 'Free', 'categories': ['Technology'],
                'is_virtual': True, 'requires_registration': True,
            })
        except (requests.RequestException, ValueError):
            continue
    return events
