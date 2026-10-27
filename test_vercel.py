"""Small offline smoke test for the scheduled scraper and stable Firestore IDs."""
import os
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

from database import Database
from event_scraper import EventScraper
from firestoreservice import EventStore


def test_scraping_and_ids():
    with tempfile.TemporaryDirectory() as folder:
        scraper = EventScraper(Database(f'{folder}/events.db'))
        scraper.serverless = True
        class Reply:
            text = '<rss><channel><item><title>AI Biology Seminar</title><link>https://example.org/talk</link><pubDate>Tue, 10 Nov 2026 14:00:00 GMT</pubDate></item></channel></rss>'
            def raise_for_status(self):
                pass
        with patch.object(scraper.session, 'get', return_value=Reply()):
            events = scraper.scrape_website('https://example.org/feed')
        assert len(events) == 1, events
        assert events[0]['title'] == 'AI Biology Seminar'
        with patch.object(scraper.session, 'get', return_value=Reply()):
            assert len(scraper.scrape_website('https://example.org/feed')) == 1
        assert EventStore._document_id(events[0]) == EventStore._document_id(dict(events[0]))
        with patch.object(scraper.session, 'get', side_effect=TimeoutError('unavailable')):
            try:
                scraper.scrape_website('https://example.org/feed')
            except TimeoutError:
                pass
            else:
                raise AssertionError('Scrape failures must not be reported as success')


def test_cron_auth():
    import app as site
    with patch.dict(os.environ, {'CRON_SECRET': 'test-secret'}):
        client = site.app.test_client()
        assert client.get('/api/cron/scrape').status_code == 401
        assert client.get('/api/cron/scrape', headers={'Authorization': 'Bearer wrong'}).status_code == 401
        event = {'title': 'AI Biology Seminar', 'date': '2026-11-10', 'url': 'https://example.org/talk', 'source_url': 'https://example.org/feed'}
        class Worker:
            websites = ['https://example.org/feed']
            def __init__(self, database):
                pass
            def scrape_website(self, site_url):
                return [dict(event)]
        written = []
        store = SimpleNamespace(upsert_events=lambda events: written.extend(events) or len(events))
        with patch.object(site, 'USE_FIRESTORE', True), patch.object(site, 'EventScraper', Worker), patch.object(site, 'event_store', store), patch.object(site, '_refresh_computing_events', return_value=2):
            response = client.get('/api/cron/scrape', headers={'Authorization': 'Bearer test-secret'})
        assert response.status_code == 200, response.json
        assert response.json['events'] == 1
        assert response.json['computing_events'] == 2
        assert written[0]['categories']


def test_free_computing_events():
    import json
    import computing_scraper as scraper
    listing = ''.join(f'<div>Free registration <a href="https://gdg.community.dev/events/details/{slug}/">View details</a></div>'
                      for slug in ('boston', 'virtual', 'paid', 'remote'))
    places = {'boston': {'@type': 'Place', 'name': 'Workshop Center', 'address': {'addressLocality': 'Boston'}},
              'virtual': {'@type': 'VirtualLocation', 'url': 'https://meet.example.org'},
              'paid': {'@type': 'VirtualLocation'},
              'remote': {'@type': 'Place', 'name': 'New York'}}
    class FakeSession:
        def get(self, url, timeout):
            slug = url.rstrip('/').split('/')[-1]
            if slug == 'gdg-cloud-boston':
                body = listing
            else:
                event = {'@type': 'Event', 'name': slug, 'startDate': '2099-11-21T12:00:00Z', 'location': places[slug]}
                if slug == 'paid':
                    event['offers'] = {'price': '45'}
                body = f'<script type="application/ld+json">{json.dumps(event)}</script>'
            return SimpleNamespace(content=body.encode(), raise_for_status=lambda: None)
    with patch.object(scraper, 'SOURCES', (scraper.SOURCES[0],)), patch.object(scraper, 'VIRTUAL_EVENTS', ()):
        events = scraper.scrape_free_events(FakeSession())
    assert {e['title'] for e in events} == {'boston', 'virtual'}
    assert all(e['cost_type'] == 'Free' for e in events)


def test_calendar_duplicates():
    from event_dedupe import unique_events
    base = {'title': 'Colloquium: Dr. Jane Doe on Neural Circuits', 'date': '2099-11-21',
            'time': '2:00 PM', 'url': 'https://example.org/events', 'source_url': 'https://example.org/events',
            'description': 'Short'}
    detail = dict(base, title='Colloquium – Dr Jane Doe on Neural Circuits',
                  url='https://example.org/talk/jane', description='A detailed description.')
    different = dict(base, title='Dr Jane Doe: New work on Protein Design')
    unknown = dict(base, time='Time TBD', title='Details to come')
    kept = unique_events([base, detail, different, unknown, dict(unknown)])
    assert len(kept) == 4  # Same speaker, different topic must remain; unknown times must not merge.
    assert kept[0]['url'] == detail['url']
    assert len(unique_events([detail, dict(detail)])) == 1


def test_official_free_virtual_events():
    import computing_scraper as scraper
    pages = {
        'githubuniverse.com': '<title>GitHub Universe 2099</title>October 28–29 Register virtually for free. Paid in-person tickets.',
        'aws.amazon.com': '<title>AWS re:Invent 2099</title>Register for the free livestream. Nov. 30 – Dec. 4',
    }
    class FakeSession:
        def get(self, url, timeout):
            body = pages[next(host for host in pages if host in url)]
            return SimpleNamespace(content=body.encode(), raise_for_status=lambda: None)
    with patch.object(scraper, 'SOURCES', ()):
        events = scraper.scrape_free_events(FakeSession())
        assert {e['host'] for e in events} == {'GitHub', 'Amazon Web Services'}
        assert all(e['is_virtual'] and e['cost_type'] == 'Free' for e in events)
        pages['githubuniverse.com'] = '<title>GitHub Universe 2099</title>October 28–29 Free ticket giveaway; in-person tickets $100.'
        pages['aws.amazon.com'] = '<title>AWS re:Invent 2099</title>Register for the free livestream. November 9 registration opens.'
        assert scraper.scrape_free_events(FakeSession()) == []


if __name__ == '__main__':
    test_scraping_and_ids()
    test_cron_auth()
    test_free_computing_events()
    test_official_free_virtual_events()
    test_calendar_duplicates()
