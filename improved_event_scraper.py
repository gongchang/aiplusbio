#!/usr/bin/env python3
"""
Improved event scraper with better URL validation and date parsing.
This script enhances the existing event scraper with better validation.
"""

import requests
from bs4 import BeautifulSoup
import json
import feedparser
from datetime import datetime, timedelta
import re
import time
import schedule
import threading
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import logging


class ImprovedEventScraper:
    def __init__(self, database):
        self.db = database
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Handle SSL certificate issues
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def validate_event_url(self, url: str, source_url: str = None) -> tuple[bool, str]:
        """
        Validate if a URL points to a valid event page.
        Returns (is_valid, reason)
        """
        try:
            # Basic URL validation
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            # Check if URL is the same as source (generic listing page)
            if source_url and url == source_url:
                return False, "Same as source URL (generic listing)"
            
            # Check for generic URL patterns that indicate listing pages
            generic_patterns = [
                '/events/',
                '/events',
                '/calendar/',
                '/calendar',
                '/upcoming-events',
                '/all-events',
                '/event-listings',
                '/search',
                '/filter',
                '/archive/',
                '/past'
            ]
            
            url_lower = url.lower()
            for pattern in generic_patterns:
                if pattern in url_lower and url_lower.endswith(pattern):
                    return False, f"Generic listing page pattern: {pattern}"
            
            # Test URL accessibility
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code not in [200, 301, 302]:
                    return False, f"HTTP {response.status_code}"
            except requests.exceptions.Timeout:
                return False, "Request timeout"
            except requests.exceptions.ConnectionError:
                return False, "Connection error"
            except Exception as e:
                return False, f"Request error: {str(e)}"
            
            return True, "Valid URL"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def validate_event_title(self, title: str) -> tuple[bool, str]:
        """
        Validate if a title is meaningful and not generic.
        Returns (is_valid, reason)
        """
        if not title or not title.strip():
            return False, "Empty title"
        
        title = title.strip()
        
        # Check for generic titles
        generic_titles = [
            'Event', 'Events', 'TBA', 'TBD', 'To be announced', 'To be determined',
            'Events Search and Views Navigation', 'Navigation', 'Search',
            'Upcoming Events', 'All Events', 'Event Listings'
        ]
        
        if title in generic_titles:
            return False, f"Generic title: {title}"
        
        # Check for generic patterns
        generic_patterns = [
            r'^Event\s*$',
            r'^Events\s*$',
            r'^TBA\s*$',
            r'^TBD\s*$',
            r'.*Navigation.*',
            r'.*Search.*',
            r'.*\d{4}.*Seminar.*',  # Like "October 2, 2025Seminar"
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # Just a date
            r'^\w+\s+\d{1,2},\s+\d{4}$'  # Like "October 2, 2025"
        ]
        
        for pattern in generic_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                return False, f"Generic title pattern: {pattern}"
        
        # Check if title is too short
        if len(title) < 5:
            return False, "Title too short"
        
        # Check if title is mostly punctuation or numbers
        if len(re.sub(r'[^\w\s]', '', title)) < 3:
            return False, "Title contains too little meaningful text"
        
        return True, "Valid title"
    
    def validate_event_date(self, date_str: str) -> tuple[bool, str, str]:
        """
        Validate and normalize event date.
        Returns (is_valid, reason, normalized_date)
        """
        if not date_str or not date_str.strip():
            return False, "Empty date", ""
        
        date_str = date_str.strip()
        
        # Check if it's already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                if parsed_date.date() >= datetime.now().date():
                    return True, "Valid future date", date_str
                else:
                    return False, "Past date", ""
            except ValueError:
                return False, "Invalid date format", ""
        
        # Try to parse other formats
        date_patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%m-%d-%Y'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', '%B %d %Y'),
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})', '%b %d %Y'),
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(st|nd|rd|th),?\s+(\d{4})', '%B %d %Y'),
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(st|nd|rd|th),?\s+(\d{4})', '%b %d %Y')
        ]
        
        for pattern, format_str in date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    # Extract the date parts
                    if format_str == '%m/%d/%Y':
                        date_str_parsed = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
                    elif format_str == '%m-%d-%Y':
                        date_str_parsed = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    elif format_str == '%Y-%m-%d':
                        date_str_parsed = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    elif format_str == '%B %d %Y':
                        date_str_parsed = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    elif format_str == '%b %d %Y':
                        date_str_parsed = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    
                    # Parse the date
                    parsed_date = datetime.strptime(date_str_parsed, format_str)
                    
                    # Only return future dates
                    today = datetime.now().date()
                    if parsed_date.date() >= today:
                        return True, "Valid future date", parsed_date.strftime('%Y-%m-%d')
                    else:
                        # If it's a past date, try next year
                        next_year_date = parsed_date.replace(year=parsed_date.year + 1)
                        if next_year_date.date() >= today:
                            return True, "Valid future date (next year)", next_year_date.strftime('%Y-%m-%d')
                        
                except ValueError:
                    continue
        
        # Handle month-only dates like "June", "Nov"
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month_lower = date_str.lower().strip()
        if month_lower in month_map:
            month = month_map[month_lower]
            current_year = datetime.now().year
            if month < datetime.now().month:
                current_year += 1
            normalized_date = f"{current_year}-{month:02d}-01"
            return True, "Month-only date (set to first day)", normalized_date
        
        return False, "Could not parse date", ""
    
    def extract_best_event_url(self, element, source_url: str, title: str) -> str:
        """Enhanced URL extraction with validation"""
        
        # Find all links in the element
        links = element.find_all('a', href=True)
        
        if not links:
            return source_url
        
        # Score each link based on relevance
        best_url = source_url
        best_score = 0
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            link_title = link.get('title', '').lower()
            
            # Skip empty or invalid URLs
            if not href or href.startswith('#'):
                continue
            
            # Build full URL
            full_url = urljoin(source_url, href)
            
            # Validate URL first
            is_valid, reason = self.validate_event_url(full_url, source_url)
            if not is_valid:
                continue
            
            # Score the link
            score = 0
            
            # Higher score for links that contain event-related keywords
            event_keywords = ['event', 'detail', 'more', 'read', 'learn', 'register', 'rsvp', 'info']
            for keyword in event_keywords:
                if keyword in link_text or keyword in link_title:
                    score += 2
            
            # Higher score for links that contain words from the event title
            if title:
                title_words = title.lower().split()
                for word in title_words:
                    if len(word) > 3 and (word in link_text or word in link_title):
                        score += 1
            
            # Higher score for links that look like event detail pages
            url_lower = full_url.lower()
            if any(pattern in url_lower for pattern in ['/event/', '/events/', '/detail', '/view']):
                score += 3
            
            # Lower score for generic navigation links
            generic_patterns = ['/about', '/contact', '/home', '/index', '/news', '/blog']
            if any(pattern in url_lower for pattern in generic_patterns):
                score -= 2
            
            # Prefer links with meaningful text over generic ones
            if len(link_text) > 5 and link_text not in ['click here', 'read more', 'learn more']:
                score += 1
            
            # Update best URL if this one has a higher score
            if score > best_score:
                best_score = score
                best_url = full_url
        
        return best_url
    
    def extract_event_from_element_improved(self, element, source_url: str, soup: BeautifulSoup = None) -> Dict[str, Any]:
        """Enhanced event extraction with validation"""
        try:
            # Extract title with better logic
            title = self.extract_better_title(element)
            
            # Validate title
            title_valid, title_reason = self.validate_event_title(title)
            if not title_valid:
                self.logger.debug(f"Skipping event with invalid title: {title_reason}")
                return None
            
            # Extract description
            description = self.extract_description(element)
            
            # Extract date and time
            date_text = element.get_text()
            date = self.extract_date_from_text(date_text)
            
            # Validate date
            date_valid, date_reason, normalized_date = self.validate_event_date(date)
            if not date_valid:
                self.logger.debug(f"Skipping event with invalid date: {date_reason}")
                return None
            
            # Prefer structured time extraction within element or page-level JSON-LD
            time = self.extract_time_from_element(element, soup) or self.extract_time_from_text(date_text)
            
            # Extract location
            location = self.extract_location(element)
            
            # Extract URL with improved logic
            url = self.extract_best_event_url(element, source_url, title)
            
            # Validate URL
            url_valid, url_reason = self.validate_event_url(url, source_url)
            if not url_valid:
                self.logger.debug(f"Skipping event with invalid URL: {url_reason}")
                return None
            
            # Detect virtual/registration
            full_text = element.get_text()
            is_virtual = self.detect_virtual_event(full_text)
            requires_registration = self.detect_registration_required(full_text)
            
            return {
                'title': title,
                'description': description,
                'date': normalized_date,
                'time': time,
                'location': location,
                'url': url,
                'source_url': source_url,
                'is_virtual': is_virtual,
                'requires_registration': requires_registration,
                'categories': []
            }
        
        except Exception as e:
            self.logger.error(f"Error extracting event: {str(e)}")
        
        return None
    
    # Include other methods from the original EventScraper class
    def extract_better_title(self, element) -> str:
        """Extract title with improved logic to avoid date/time titles"""
        
        # Special handling for iaifi.org structure
        if element.name == 'li':
            # Look for <em> tags which contain the talk titles
            em_tag = element.find('em')
            if em_tag:
                title = em_tag.get_text(strip=True)
                if title and not self.is_date_time_title(title):
                    return title
            
            # Look for speaker names in <strong> tags with links
            strong_tag = element.find('strong')
            if strong_tag:
                # Extract speaker name from the link text
                link = strong_tag.find('a')
                if link:
                    speaker_name = link.get_text(strip=True)
                    if speaker_name and not self.is_date_time_title(speaker_name):
                        return speaker_name
        
        # Try specific title selectors first
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5',
            '.title', '.event-title', '.event-name',
            '[class*="title"]', '[class*="event-title"]',
            '.headline', '.event-headline', 'em'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and not self.is_date_time_title(title):
                    return title
        
        # Try to find title in description or other text elements
        desc_selectors = ['.description', '.summary', '.content', 'p', '.event-description']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                # Look for the first sentence that looks like a title
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if (len(sentence) > 10 and len(sentence) < 200 and 
                        not self.is_date_time_title(sentence)):
                        return sentence
        
        # Last resort: try to extract meaningful text from the element
        full_text = element.get_text(strip=True)
        lines = full_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and len(line) < 200 and 
                not self.is_date_time_title(line)):
                return line
        
        return ""
    
    def is_date_time_title(self, text: str) -> bool:
        """Check if text looks like a date/time instead of a title"""
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Check for date/time patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}',
            r'\d{1,2}:\d{2}\s*(am|pm)',
            r'@\s*\d{1,2}:\d{2}',
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check if text is mostly numbers and common date/time words
        words = text.split()
        if len(words) <= 3:
            date_time_words = ['am', 'pm', 'at', '@', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
            date_time_count = sum(1 for word in words if word.lower() in date_time_words or word.isdigit())
            if date_time_count >= len(words) * 0.7:  # 70% or more are date/time words
                return True
        
        return False
    
    def extract_description(self, element) -> str:
        """Extract description from element"""
        desc_selectors = ['.description', '.summary', '.content', 'p', '.event-description']
        for selector in desc_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(strip=True)
        return ""
    
    def extract_location(self, element) -> str:
        """Extract location from element"""
        location_selectors = ['.location', '.venue', '.address', '[class*="location"]']
        for selector in location_selectors:
            loc_elem = element.select_one(selector)
            if loc_elem:
                return loc_elem.get_text(strip=True)
        return ""
    
    def extract_date_from_text(self, text: str) -> str:
        """Extract date from text using various patterns"""
        # This will be enhanced with the validation logic
        return text  # Placeholder
    
    def extract_time_from_element(self, element, soup: BeautifulSoup = None) -> str:
        """Extract time from element"""
        return ""  # Placeholder
    
    def extract_time_from_text(self, text: str) -> str:
        """Extract time from text"""
        return ""  # Placeholder
    
    def detect_virtual_event(self, text: str) -> bool:
        """Detect if an event is virtual"""
        virtual_keywords = [
            'virtual', 'online', 'zoom', 'webinar', 'webcast', 'streaming',
            'remote', 'digital', 'live stream', 'livestream'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in virtual_keywords)
    
    def detect_registration_required(self, text: str) -> bool:
        """Detect if registration is required"""
        registration_keywords = [
            'register', 'registration', 'rsvp', 'sign up', 'signup',
            'required', 'mandatory', 'book', 'reserve'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in registration_keywords)


def main():
    """Test the improved event scraper"""
    from database import Database
    
    db = Database()
    scraper = ImprovedEventScraper(db)
    
    # Test validation functions
    test_cases = [
        ("Google Cloud Next 2025", "Valid event title"),
        ("Event", "Generic title"),
        ("TBA", "Generic title"),
        ("October 2, 2025Seminar", "Date-time title"),
        ("", "Empty title"),
        ("AI Conference 2025", "Valid event title")
    ]
    
    print("Testing title validation:")
    for title, expected in test_cases:
        is_valid, reason = scraper.validate_event_title(title)
        print(f"  '{title}': {is_valid} - {reason}")
    
    # Test URL validation
    test_urls = [
        ("https://cloud.withgoogle.com/next", "Valid event URL"),
        ("https://example.com/events/", "Generic listing URL"),
        ("https://example.com/event/123", "Valid specific event URL"),
        ("https://example.com/calendar", "Generic calendar URL")
    ]
    
    print("\nTesting URL validation:")
    for url, expected in test_urls:
        is_valid, reason = scraper.validate_event_url(url)
        print(f"  '{url}': {is_valid} - {reason}")
    
    # Test date validation
    test_dates = [
        ("2025-10-10", "Valid ISO date"),
        ("October 10, 2025", "Valid text date"),
        ("10/10/2025", "Valid US date"),
        ("June", "Month only"),
        ("2024-01-01", "Past date"),
        ("", "Empty date")
    ]
    
    print("\nTesting date validation:")
    for date_str, expected in test_dates:
        is_valid, reason, normalized = scraper.validate_event_date(date_str)
        print(f"  '{date_str}': {is_valid} - {reason} -> {normalized}")


if __name__ == "__main__":
    main()



