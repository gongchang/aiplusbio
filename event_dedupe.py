"""Collapse duplicate calendar cards without deleting source records."""
import re
from urllib.parse import urlparse


def unique_events(events):
    result, by_slot = [], {}
    for event in events:
        label = (event.get('title') or '').strip().casefold()
        if (not label or label in ('campus map', 'media inquiries', 'public colloquia', 'details to come.',
                                    'events | brain and cognitive sciences', 'events - mit department of biology')):
            continue
        title = set(re.findall(r'\w+', label))
        date = event.get('date')
        time = (event.get('time') or '').strip().lower()
        # Unknown-time events may be different talks; only dedupe with an event URL.
        reliable_time = time not in ('', 'time tbd', 'tbd', 'unknown')
        url = event.get('url') or ''
        url_path = (urlparse(url).netloc, urlparse(url).path.rstrip('/'))
        slot = (date, time) if reliable_time else (date, 'undated-time')
        found = None
        for index in by_slot.get(slot, []):
            existing = result[index]
            old_title = set(re.findall(r'\w+', (existing.get('title') or '').casefold()))
            old_url = existing.get('url') or ''
            same_detail = bool(url_path[1] and url_path[1] not in ('/events', '/seminars')
                               and url_path == (urlparse(old_url).netloc, urlparse(old_url).path.rstrip('/')))
            similar_title = (reliable_time and
                             ((len(title) >= 4 and len(old_title) >= 4 and
                               len(title & old_title) / min(len(title), len(old_title)) >= .82)
                              or (event.get('source_url') == existing.get('source_url') and
                                  len(title & old_title) >= 2 and
                                  len(title & old_title) == min(len(title), len(old_title)) and
                                  max(len(title), len(old_title)) >= min(len(title), len(old_title)) + 3)))
            # A series can run different sessions at the same hour; keep distinct topics.
            old_label = (existing.get('title') or '').casefold()
            if ':' in label and ':' in old_label and label.split(':', 1)[0] == old_label.split(':', 1)[0] and label.split(':', 1)[1] != old_label.split(':', 1)[1]:
                similar_title = False
            if same_detail or similar_title:
                found = index
                break
        if found is None:
            by_slot.setdefault(slot, []).append(len(result))
            result.append(event)
        else:
            old = result[found]
            # Prefer a detail link over a source listing; then fuller descriptions.
            quality = lambda e: (bool(e.get('url') and e.get('url') != e.get('source_url')),
                                 len(e.get('title') or ''), len(e.get('description') or ''))
            if quality(event) > quality(old):
                result[found] = event
    return result
