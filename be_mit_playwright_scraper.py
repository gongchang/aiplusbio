#!/usr/bin/env python3
"""
BE MIT Seminars scraper using Playwright for JavaScript rendering
"""

import asyncio
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BEMITPlaywrightScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def setup_browser(self):
        """Setup Playwright browser with SSL bypass"""
        try:
            from playwright.async_api import async_playwright
            
            logger.info("🚀 Setting up Playwright browser...")
            
            self.playwright = await async_playwright().start()
            
            # Launch browser with SSL bypass
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors'
                ]
            )
            
            self.page = await self.browser.new_page()
            
            # Set SSL bypass for the page
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Ignore HTTPS errors
            self.page.set_default_timeout(30000)
            
            logger.info("✅ Browser setup complete")
            return True
            
        except ImportError:
            logger.error("❌ Playwright not installed. Install with: pip install playwright")
            return False
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    async def wait_for_angular(self, timeout=30):
        """Wait for Angular.js to finish rendering"""
        try:
            logger.info("⏳ Waiting for Angular.js to finish rendering...")
            
            # Wait for Angular to be ready
            await self.page.wait_for_function(
                'window.angular && angular.element(document.body).scope()',
                timeout=timeout * 1000
            )
            
            # Wait for Angular to finish digest cycle
            await self.page.evaluate('''
                () => {
                    if (window.angular) {
                        var scope = angular.element(document.body).scope();
                        if (scope && scope.$apply) {
                            scope.$apply();
                        }
                    }
                }
            ''')
            
            # Additional wait for any pending operations
            await asyncio.sleep(2)
            
            logger.info("✅ Angular.js rendering complete")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Angular.js wait failed: {e}")
            return False
    
    async def handle_load_more(self):
        """Handle 'Load More' buttons if present"""
        try:
            logger.info("🔍 Looking for 'Load More' buttons...")
            
            # Multiple selectors for load more buttons
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                'a:has-text("Load More")',
                'a:has-text("Show More")',
                '[class*="load-more"]',
                '[class*="show-more"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    # Check if button exists
                    button = self.page.locator(selector)
                    if await button.count() > 0:
                        logger.info(f"🔄 Found load more button: {selector}")
                        
                        # Click the button
                        await button.first.click()
                        
                        # Wait for new content to load
                        await asyncio.sleep(3)
                        
                        # Wait for Angular to update
                        await self.wait_for_angular(10)
                        
                        logger.info("✅ Load more content loaded")
                        return True
                        
                except Exception as e:
                    continue
            
            logger.info("ℹ️  No load more buttons found")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️  Load more handling failed: {e}")
            return False
    
    async def extract_events_with_multiple_strategies(self):
        """Extract events using multiple selector strategies"""
        events = []
        
        # Strategy 1: Angular-specific selectors
        angular_selectors = [
            '[ng-repeat*="seminar"]',
            '[ng-repeat*="event"]',
            '[ng-repeat*="item"]',
            '[data-ng-repeat*="seminar"]',
            '[data-ng-repeat*="event"]'
        ]
        
        # Strategy 2: Standard CSS selectors
        css_selectors = [
            '.seminar-item',
            '.event-item',
            '.seminar',
            '.event',
            '[class*="seminar"]',
            '[class*="event"]',
            'article',
            '.card',
            '.item'
        ]
        
        # Strategy 3: Table-based selectors
        table_selectors = [
            'table tr',
            '.table tr',
            '[class*="table"] tr'
        ]
        
        all_selectors = angular_selectors + css_selectors + table_selectors
        
        logger.info(f"🔍 Trying {len(all_selectors)} different selectors...")
        
        for selector in all_selectors:
            try:
                logger.info(f"🔍 Trying selector: {selector}")
                
                # Get elements with this selector
                elements = self.page.locator(selector)
                count = await elements.count()
                
                if count > 0:
                    logger.info(f"✅ Found {count} elements with selector: {selector}")
                    
                    for i in range(min(count, 20)):  # Limit to first 20 elements
                        try:
                            element = elements.nth(i)
                            
                            # Extract text content
                            text_content = await element.text_content()
                            
                            # Extract HTML content for better parsing
                            html_content = await element.inner_html()
                            
                            # Parse with BeautifulSoup for better extraction
                            soup = BeautifulSoup(html_content, 'html.parser')
                            
                            # Extract event information
                            event = self.extract_event_from_element(soup, text_content)
                            
                            if event:
                                events.append(event)
                                logger.info(f"✅ Extracted event: {event['title'][:50]}...")
                            
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to extract from element: {e}")
                            continue
                    
                    # If we found events with this selector, break
                    if events:
                        break
                        
            except Exception as e:
                logger.warning(f"⚠️  Selector {selector} failed: {e}")
                continue
        
        # Strategy 4: Text pattern matching (fallback)
        if not events:
            logger.info("🔍 Trying text pattern matching...")
            events = await self.extract_events_by_text_patterns()
        
        return events
    
    def extract_event_from_element(self, soup, text_content):
        """Extract event information from a BeautifulSoup element"""
        try:
            # Extract title from various elements
            title = None
            title_elements = [
                soup.find('h1'), soup.find('h2'), soup.find('h3'),
                soup.find('h4'), soup.find('h5'), soup.find('h6'),
                soup.find('a'), soup.find('strong'), soup.find('b'),
                soup.find('span', class_=re.compile(r'title|name', re.I))
            ]
            
            for elem in title_elements:
                if elem and elem.get_text(strip=True):
                    potential_title = elem.get_text(strip=True)
                    if potential_title.lower() not in ['seminar', 'event', 'seminars', 'events']:
                        title = potential_title
                        break
            
            if not title:
                # Try to extract from text content
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                for line in lines:
                    if line and len(line) > 10 and line.lower() not in ['seminar', 'event', 'seminars', 'events']:
                        title = line
                        break
            
            if not title:
                return None
            
            # Extract date using multiple patterns
            date = None
            date_patterns = [
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{1,2}-\d{1,2}-\d{4}\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.I)
                if match:
                    date = match.group()
                    break
            
            if not date:
                return None
            
            # Extract URL
            link = soup.find('a', href=True)
            url = urljoin("https://be.mit.edu/our-community/seminars/", link['href']) if link else "https://be.mit.edu/our-community/seminars/"
            
            return {
                'title': title,
                'date': date,
                'url': url,
                'description': "",
                'source_url': "https://be.mit.edu/our-community/seminars/"
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Event extraction failed: {e}")
            return None
    
    async def extract_events_by_text_patterns(self):
        """Extract events by analyzing text patterns in the page"""
        try:
            logger.info("🔍 Extracting events by text patterns...")
            
            # Get all text content
            text_content = await self.page.text_content('body')
            
            events = []
            
            # Split into lines and look for patterns
            lines = text_content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for lines with dates
                date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', line)
                if date_match and len(line) > 20:
                    date = date_match.group()
                    
                    # Extract title (remove date and common words)
                    title = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', line).strip()
                    title = re.sub(r'\b(seminar|event|talk|lecture)\b', '', title, flags=re.I).strip()
                    
                    if title and len(title) > 10:
                        events.append({
                            'title': title,
                            'date': date,
                            'url': "https://be.mit.edu/our-community/seminars/",
                            'description': "",
                            'source_url': "https://be.mit.edu/our-community/seminars/"
                        })
            
            logger.info(f"✅ Extracted {len(events)} events by text patterns")
            return events
            
        except Exception as e:
            logger.error(f"❌ Text pattern extraction failed: {e}")
            return []
    
    async def scrape_be_mit_seminars(self):
        """Main scraping function for BE MIT Seminars"""
        logger.info("🚀 Starting BE MIT Seminars scraping...")
        
        if not await self.setup_browser():
            logger.error("❌ Browser setup failed")
            return []
        
        try:
            # Navigate to the page
            url = "https://be.mit.edu/our-community/seminars/"
            logger.info(f"🌐 Navigating to: {url}")
            
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for initial page load
            await asyncio.sleep(3)
            
            # Wait for Angular.js to finish rendering
            await self.wait_for_angular(30)
            
            # Handle load more buttons
            await self.handle_load_more()
            
            # Extract events using multiple strategies
            events = await self.extract_events_with_multiple_strategies()
            
            logger.info(f"✅ Scraping complete. Found {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            return []
        
        finally:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
    
    def add_events_to_database(self, events):
        """Add events to the database"""
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        added_count = 0
        
        for event in events:
            try:
                # Check if event already exists
                cursor.execute("""
                    SELECT id FROM events 
                    WHERE title = ? AND date = ? AND source_url = ?
                """, (event['title'], event['date'], event['source_url']))
                
                if cursor.fetchone() is None:
                    # Add new event
                    cursor.execute("""
                        INSERT INTO events (title, description, date, time, location, url, source_url, is_virtual, requires_registration, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event['title'],
                        event['description'],
                        event['date'],
                        '',  # time
                        '',  # location
                        event['url'],
                        event['source_url'],
                        False,  # is_virtual
                        False,  # requires_registration
                        datetime.now()
                    ))
                    added_count += 1
                    
            except Exception as e:
                logger.error(f"Error adding event {event['title']}: {e}")
        
        conn.commit()
        conn.close()
        
        return added_count

async def main():
    """Main function to run the scraper"""
    print("🚀 Advanced BE MIT Seminars Scraper (Playwright)")
    print("=" * 50)
    
    scraper = BEMITPlaywrightScraper()
    
    # Run the scraper
    events = await scraper.scrape_be_mit_seminars()
    
    if events:
        print(f"💾 Adding {len(events)} events to database...")
        added_count = scraper.add_events_to_database(events)
        print(f"✅ Added {added_count} new events to database")
        
        # Show some examples
        print("\n📋 Sample events:")
        for event in events[:5]:
            print(f"  • {event['title']} ({event['date']})")
    else:
        print("❌ No events found")

if __name__ == "__main__":
    # Install playwright if not available
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("📦 Installing playwright...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright installed")
    
    # Run the scraper
    asyncio.run(main())
