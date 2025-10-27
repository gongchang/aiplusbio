#!/usr/bin/env python3
"""
Update the event scraper with improved URL extraction logic
"""

import re

def update_scraper():
    """Update the event_scraper.py with improved extraction methods"""
    
    print("🔧 Updating Event Scraper with Improved Logic...")
    
    # Read the current event_scraper.py
    with open('event_scraper.py', 'r') as f:
        content = f.read()
    
    # Find the extract_event_from_element method and replace it
    old_method = '''    def extract_event_from_element(self, element, source_url: str) -> Dict[str, Any]:
        """Extract event information from a DOM element"""
        try:
            # Extract title
            title = ''
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.event-title', '[class*="title"]']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = element.get_text(strip=True)[:100]  # Fallback
            
            # Extract description
            description = ''
            desc_selectors = ['.description', '.summary', '.content', 'p']
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break
            
            # Extract date
            date_text = element.get_text()
            date = self.extract_date_from_text(date_text)
            
            # Extract time
            time_text = element.get_text()
            time = self.extract_time_from_text(time_text)
            
            # Extract location
            location = ''
            location_selectors = ['.location', '.venue', '.address', '[class*="location"]']
            for selector in location_selectors:
                loc_elem = element.select_one(selector)
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    break
            
            # Extract URL
            url = source_url
            link_elem = element.find('a')
            if link_elem and link_elem.get('href'):
                url = urljoin(source_url, link_elem.get('href'))
            
            # Detect virtual/registration
            full_text = element.get_text()
            is_virtual = self.detect_virtual_event(full_text)
            requires_registration = self.detect_registration_required(full_text)
            
            if title and date:
                return {
                    'title': title,
                    'description': description,
                    'date': date,
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
        
        return None'''
    
    new_method = '''    def extract_event_from_element(self, element, source_url: str) -> Dict[str, Any]:
        """Extract event information from a DOM element with improved logic"""
        try:
            # Extract title with better logic
            title = self.extract_better_title(element)
            
            # Extract description
            description = self.extract_description(element)
            
            # Extract date and time
            date_text = element.get_text()
            date = self.extract_date_from_text(date_text)
            time = self.extract_time_from_text(date_text)
            
            # Extract location
            location = self.extract_location(element)
            
            # Extract URL with improved logic
            url = self.extract_best_event_url(element, source_url, title)
            
            # Detect virtual/registration
            full_text = element.get_text()
            is_virtual = self.detect_virtual_event(full_text)
            requires_registration = self.detect_registration_required(full_text)
            
            if title and date and not self.is_date_time_title(title):
                return {
                    'title': title,
                    'description': description,
                    'date': date,
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
        
        return None'''
    
    # Replace the old method with the new one
    if old_method in content:
        content = content.replace(old_method, new_method)
        
        # Add the new helper methods
        new_methods = '''
    def extract_better_title(self, element) -> str:
        """Extract title with improved logic to avoid date/time titles"""
        
        # Try specific title selectors first
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5',
            '.title', '.event-title', '.event-name',
            '[class*="title"]', '[class*="event-title"]',
            '.headline', '.event-headline'
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
        lines = full_text.split('\\n')
        
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and len(line) < 200 and 
                not self.is_date_time_title(line)):
                return line
        
        return ""
    
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
    
    def extract_best_event_url(self, element, source_url: str, title: str) -> str:
        """Extract the most relevant URL for the event"""
        
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
            
            # Score the link
            score = 0
            
            # Higher score for links that contain event-related keywords
            event_keywords = ['event', 'detail', 'more', 'read', 'learn', 'register', 'rsvp']
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
    
    def is_date_time_title(self, text: str) -> bool:
        """Check if text looks like a date/time instead of a title"""
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Check for date/time patterns
        date_patterns = [
            r'\\d{1,2}/\\d{1,2}/\\d{4}',
            r'\\d{4}-\\d{2}-\\d{2}',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\\s+\\d{1,2},?\\s+\\d{4}',
            r'\\d{1,2}\\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\s+\\d{4}',
            r'\\d{1,2}:\\d{2}\\s*(am|pm)',
            r'@\\s*\\d{1,2}:\\d{2}',
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
        
        return False'''
        
        # Insert the new methods before the extract_date_from_text method
        if 'def extract_date_from_text(self, text: str) -> str:' in content:
            content = content.replace(
                '    def extract_date_from_text(self, text: str) -> str:',
                new_methods + '\\n    def extract_date_from_text(self, text: str) -> str:'
            )
        
        # Write the updated content back to the file
        with open('event_scraper.py', 'w') as f:
            f.write(content)
        
        print("✅ Successfully updated event_scraper.py with improved extraction logic")
        return True
    else:
        print("❌ Could not find the extract_event_from_element method to replace")
        return False

if __name__ == '__main__':
    if update_scraper():
        print("\\n🎉 Event scraper has been successfully updated!")
        print("💡 The improved scraper will now:")
        print("   - Extract better titles (avoid date/time as titles)")
        print("   - Find more relevant event URLs")
        print("   - Prevent future extraction issues")
        print("\\n🚀 You can now run 'python run.py' to test the improvements")
    else:
        print("\\n❌ Failed to update event scraper")
        print("💡 You may need to manually update the extract_event_from_element method")
