#!/usr/bin/env python3
"""
Advanced BE MIT Seminars scraper with Angular.js handling and SSL bypass
"""

import asyncio
import time
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BEMITSeminarsScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def setup_browser(self):
        """Setup Pyppeteer browser with SSL bypass"""
        try:
            import pyppeteer
            from pyppeteer import launch
            
            logger.info("🚀 Setting up Pyppeteer browser...")
            
            # Launch browser with SSL bypass and other optimizations
            self.browser = await launch({
                'headless': True,
                'ignoreHTTPSErrors': True,  # SSL certificate bypass
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--ignore-certificate-errors-spki-list'
                ]
            })
            
            self.page = await self.browser.newPage()
            
            # Set user agent
            await self.page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Set viewport
            await self.page.setViewport({'width': 1920, 'height': 1080})
            
            logger.info("✅ Browser setup complete")
            return True
            
        except ImportError:
            logger.error("❌ Pyppeteer not installed. Install with: pip install pyppeteer")
            return False
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    async def wait_for_angular(self, timeout=30):
        """Wait for Angular.js to finish rendering"""
        try:
            logger.info("⏳ Waiting for Angular.js to finish rendering...")
            
            # Wait for Angular to be ready
            await self.page.waitForFunction(
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
    
    async def wait_for_dynamic_content(self, selector, timeout=30):
        """Wait for dynamic content to load"""
        try:
            logger.info(f"⏳ Waiting for content with selector: {selector}")
            
            # Wait for element to appear
            await self.page.waitForSelector(selector, timeout=timeout * 1000)
            
            # Wait for content to be populated
            await self.page.waitForFunction(
                f'document.querySelector("{selector}").textContent.trim().length > 0',
                timeout=timeout * 1000
            )
            
            logger.info(f"✅ Content loaded for selector: {selector}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Content wait failed for {selector}: {e}")
            return False
    
    async def handle_load_more(self):
        """Handle 'Load More' buttons if present"""
        try:
            logger.info("🔍 Looking for 'Load More' buttons...")
            
            # Multiple selectors for load more buttons
            load_more_selectors = [
                'button:contains("Load More")',
                'button:contains("Show More")',
                'a:contains("Load More")',
                'a:contains("Show More")',
                '[class*="load-more"]',
                '[class*="show-more"]',
                '[id*="load-more"]',
                '[id*="show-more"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    # Check if button exists
                    button = await self.page.querySelector(selector)
                    if button:
                        logger.info(f"🔄 Found load more button: {selector}")
                        
                        # Click the button
                        await button.click()
                        
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
            '[data-ng-repeat*="event"]',
            '[ng-bind*="seminar"]',
            '[ng-bind*="event"]'
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
        
        # Strategy 4: List-based selectors
        list_selectors = [
            'li[class*="seminar"]',
            'li[class*="event"]',
            'ul li',
            'ol li'
        ]
        
        all_selectors = angular_selectors + css_selectors + table_selectors + list_selectors
        
        logger.info(f"🔍 Trying {len(all_selectors)} different selectors...")
        
        for selector in all_selectors:
            try:
                logger.info(f"🔍 Trying selector: {selector}")
                
                # Get elements with this selector
                elements = await self.page.querySelectorAll(selector)
                
                if elements and len(elements) > 0:
                    logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            # Extract text content
                            text_content = await self.page.evaluate('(element) => element.textContent', element)
                            
                            # Extract HTML content for better parsing
                            html_content = await self.page.evaluate('(element) => element.outerHTML', element)
                            
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
        
        # Strategy 5: Text pattern matching (fallback)
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
            text_content = await self.page.evaluate('() => document.body.textContent')
            
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
            
            await self.page.goto(url, {
                'waitUntil': 'networkidle0',
                'timeout': 30000
            })
            
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
    print("🚀 Advanced BE MIT Seminars Scraper")
    print("=" * 50)
    
    scraper = BEMITSeminarsScraper()
    
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
    # Install pyppeteer if not available
    try:
        import pyppeteer
    except ImportError:
        print("📦 Installing pyppeteer...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyppeteer"])
        print("✅ Pyppeteer installed")
    
    # Run the scraper
    asyncio.run(main())










