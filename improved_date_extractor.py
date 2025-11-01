"""
Improved Date Extractor for Tech Events
Handles various date formats and extracts actual event dates from content.
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
import calendar


class ImprovedDateExtractor:
    def __init__(self):
        self.today = datetime.now().date()
        self.current_year = self.today.year
        self.next_year = self.current_year + 1
        
        # Common date patterns with better regex
        self.date_patterns = [
            # ISO formats
            (r'(\d{4}-\d{1,2}-\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4}/\d{1,2}/\d{1,2})', '%Y/%m/%d'),
            
            # US formats
            (r'(\d{1,2}/\d{1,2}/\d{4})', '%m/%d/%Y'),
            (r'(\d{1,2}-\d{1,2}-\d{4})', '%m-%d-%Y'),
            
            # European formats
            (r'(\d{1,2}\.\d{1,2}\.\d{4})', '%d.%m.%Y'),
            
            # Full month names
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', '%B %d %Y'),
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s+(\d{4})', '%B %d %Y'),
            
            # Abbreviated month names
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})', '%b %d %Y'),
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2})\s+(\d{4})', '%b %d %Y'),
            
            # Day of week patterns
            (r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', '%A %B %d %Y'),
            (r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})', '%A %b %d %Y'),
        ]
        
        # Relative date patterns
        self.relative_patterns = [
            (r'\btomorrow\b', 1),
            (r'\bnext week\b', 7),
            (r'\bnext month\b', 30),
            (r'\bthis week\b', 3),
            (r'\bthis month\b', 15),
            (r'\bupcoming\b', 7),
            (r'\bsoon\b', 14),
        ]
        
        # Event-specific keywords that often precede dates
        self.event_date_keywords = [
            'event', 'conference', 'workshop', 'seminar', 'meeting', 'session',
            'happening', 'scheduled', 'takes place', 'occurs', 'starts',
            'begins', 'launches', 'opens', 'closes', 'ends', 'finishes',
            'on', 'at', 'from', 'until', 'through', 'during'
        ]
    
    def extract_event_date(self, title: str, description: str = '', url: str = '') -> Optional[str]:
        """Extract the most likely event date from title, description, and URL"""
        text = f"{title} {description} {url}".lower()
        
        # First, try to find explicit dates
        explicit_date = self._extract_explicit_date(text)
        if explicit_date:
            return explicit_date
        
        # Then try relative dates
        relative_date = self._extract_relative_date(text)
        if relative_date:
            return relative_date
        
        # Finally, try to infer from context
        inferred_date = self._infer_date_from_context(text)
        if inferred_date:
            return inferred_date
        
        return None
    
    def _extract_explicit_date(self, text: str) -> Optional[str]:
        """Extract explicit dates from text"""
        for pattern, date_format in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Handle different group structures
                    groups = match.groups()
                    if len(groups) == 1:
                        date_str = groups[0]
                    elif len(groups) == 3:
                        date_str = f"{groups[0]} {groups[1]} {groups[2]}"
                    elif len(groups) == 4:
                        date_str = f"{groups[1]} {groups[2]} {groups[3]}"  # Skip day of week
                    else:
                        continue
                    
                    parsed_date = datetime.strptime(date_str, date_format).date()
                    
                    # Only return future dates
                    if parsed_date >= self.today:
                        return parsed_date.isoformat()
                        
                except ValueError:
                    continue
        
        return None
    
    def _extract_relative_date(self, text: str) -> Optional[str]:
        """Extract relative dates like 'tomorrow', 'next week'"""
        for pattern, days_offset in self.relative_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                future_date = self.today + timedelta(days=days_offset)
                return future_date.isoformat()
        
        return None
    
    def _infer_date_from_context(self, text: str) -> Optional[str]:
        """Infer date from context clues"""
        # Look for year mentions
        year_matches = re.findall(r'\b(20\d{2})\b', text)
        for year_str in year_matches:
            year = int(year_str)
            if year >= self.current_year:
                # If it's the current year, assume it's in the next few months
                if year == self.current_year:
                    # Look for month indicators
                    month = self._extract_month_from_text(text)
                    if month:
                        try:
                            # Try to create a date in the future
                            future_date = date(year, month, 1)
                            if future_date >= self.today:
                                return future_date.isoformat()
                        except ValueError:
                            continue
                else:
                    # Future year, assume January
                    try:
                        future_date = date(year, 1, 1)
                        return future_date.isoformat()
                    except ValueError:
                        continue
        
        # Look for month mentions without year
        month = self._extract_month_from_text(text)
        if month:
            # Assume current or next year
            for year in [self.current_year, self.next_year]:
                try:
                    future_date = date(year, month, 1)
                    if future_date >= self.today:
                        return future_date.isoformat()
                except ValueError:
                    continue
        
        return None
    
    def _extract_month_from_text(self, text: str) -> Optional[int]:
        """Extract month number from text"""
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for month_name, month_num in month_names.items():
            if month_name in text:
                return month_num
        
        return None
    
    def extract_event_time(self, title: str, description: str = '') -> Optional[str]:
        """Extract event time from title and description"""
        text = f"{title} {description}"
        
        # Time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*[AP]M)',
            r'(\d{1,2}\s*[AP]M)',
            r'(\d{1,2}:\d{2})',
            r'(\d{1,2}:\d{2}\s*[Aa]m)',
            r'(\d{1,2}:\d{2}\s*[Pp]m)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def is_future_event(self, title: str, description: str = '') -> bool:
        """Check if the event appears to be in the future based on keywords"""
        text = f"{title} {description}".lower()
        
        # Future indicators
        future_keywords = [
            'upcoming', 'future', 'next', 'tomorrow', 'this week', 'this month',
            'soon', 'scheduled', 'planned', 'announced', 'launching', 'starting',
            'beginning', 'opening', 'commencing', 'happening', 'taking place'
        ]
        
        # Past indicators
        past_keywords = [
            'yesterday', 'last week', 'last month', 'ago', 'was', 'were',
            'completed', 'finished', 'ended', 'concluded', 'happened',
            'took place', 'occurred', 'past', 'previous'
        ]
        
        has_future = any(keyword in text for keyword in future_keywords)
        has_past = any(keyword in text for keyword in past_keywords)
        
        # If it has past keywords, it's likely past
        if has_past:
            return False
        
        # If it has future keywords, it's likely future
        if has_future:
            return True
        
        # Check for year mentions
        year_matches = re.findall(r'\b(20\d{2})\b', text)
        for year_str in year_matches:
            year = int(year_str)
            if year > self.current_year:
                return True
            elif year < self.current_year:
                return False
        
        # Default to future if no clear indicators
        return True


def test_date_extractor():
    """Test the date extractor with various examples"""
    extractor = ImprovedDateExtractor()
    
    test_cases = [
        ("AI Conference 2025", "Join us for the annual AI conference on March 15, 2025"),
        ("Machine Learning Workshop", "Workshop happening tomorrow at 2 PM"),
        ("Tech Meetup", "Next week's meetup on Tuesday"),
        ("Data Science Summit", "Summit scheduled for December 10-12, 2025"),
        ("Cloud Computing Event", "Event on Oct 30, 2025 at 3 PM"),
        ("Virtual Conference", "Conference happening this month"),
        ("AI Workshop", "Workshop on January 20, 2026"),
        ("Past Event", "This event happened yesterday"),
    ]
    
    print("Testing date extractor:")
    for title, description in test_cases:
        date = extractor.extract_event_date(title, description)
        time = extractor.extract_event_time(title, description)
        is_future = extractor.is_future_event(title, description)
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Extracted Date: {date}")
        print(f"Extracted Time: {time}")
        print(f"Is Future: {is_future}")
        print("-" * 50)


if __name__ == "__main__":
    test_date_extractor()
