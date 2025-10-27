import openai
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

class EventCategorizer:
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                logging.warning(f"OpenAI client initialization failed: {e}. Using keyword matching.")
                self.client = None
        else:
            self.client = None
            logging.warning("OpenAI API key not found. Categorization will use keyword matching.")
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Define category keywords for fallback
        self.cs_keywords = [
            'computer science', 'cs', 'artificial intelligence', 'ai', 'machine learning', 'ml',
            'data science', 'software engineering', 'programming', 'algorithm', 'computing',
            'robotics', 'computer vision', 'natural language processing', 'nlp', 'deep learning',
            'neural network', 'database', 'system', 'network', 'cybersecurity', 'blockchain',
            'cloud computing', 'distributed system', 'optimization', 'computational'
        ]
        
        self.biology_keywords = [
            'biology', 'biological', 'biochemistry', 'biotechnology', 'genetics', 'genomics',
            'molecular biology', 'cell biology', 'microbiology', 'immunology', 'neuroscience',
            'bioinformatics', 'biomedical', 'biophysics', 'ecology', 'evolution', 'protein',
            'dna', 'rna', 'enzyme', 'metabolism', 'pathway', 'organism', 'species', 'phylogeny',
            'transcriptomics', 'proteomics', 'metabolomics', 'synthetic biology', 'crispr'
        ]
    
    def categorize_event(self, event: Dict[str, Any]) -> List[str]:
        """Categorize an event using AI or keyword matching"""
        categories = []
        
        # Prepare text for analysis
        text_to_analyze = f"{event.get('title', '')} {event.get('description', '')}"
        
        if self.client:
            # Use OpenAI API for categorization
            try:
                categories = self.categorize_with_ai(text_to_analyze)
            except Exception as e:
                self.logger.error(f"AI categorization failed: {str(e)}")
                categories = self.categorize_with_keywords(text_to_analyze)
        else:
            # Use keyword matching
            categories = self.categorize_with_keywords(text_to_analyze)
        
        return categories
    
    def categorize_with_ai(self, text: str) -> List[str]:
        """Use OpenAI API to categorize event text"""
        try:
            prompt = f"""
            Analyze the following event description and categorize it into one or both of these categories:
            - "computer science" (for events related to computing, AI, software, algorithms, etc.)
            - "biology" (for events related to biological sciences, genetics, biochemistry, etc.)
            
            Event text: "{text}"
            
            Respond with only the category names separated by commas. If neither category fits, respond with "other".
            Examples:
            - "computer science"
            - "biology"
            - "computer science, biology"
            - "other"
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that categorizes academic events."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            categories = []
            if 'computer science' in result:
                categories.append('computer science')
            if 'biology' in result:
                categories.append('biology')
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Error in AI categorization: {str(e)}")
            return self.categorize_with_keywords(text)
    
    def categorize_with_keywords(self, text: str) -> List[str]:
        """Use keyword matching to categorize event text"""
        text_lower = text.lower()
        categories = []
        
        # Check for computer science keywords
        cs_matches = sum(1 for keyword in self.cs_keywords if keyword in text_lower)
        if cs_matches >= 1:
            categories.append('computer science')
        
        # Check for biology keywords
        bio_matches = sum(1 for keyword in self.biology_keywords if keyword in text_lower)
        if bio_matches >= 1:
            categories.append('biology')
        
        return categories
    
    def batch_categorize_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize multiple events efficiently"""
        categorized_events = []
        
        for event in events:
            categories = self.categorize_event(event)
            event['categories'] = categories
            categorized_events.append(event)
        
        return categorized_events
    
    def get_categorization_stats(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about event categorization"""
        stats = {
            'total_events': len(events),
            'computer_science': 0,
            'biology': 0,
            'both_categories': 0,
            'uncategorized': 0
        }
        
        for event in events:
            categories = event.get('categories', [])
            
            if 'computer science' in categories and 'biology' in categories:
                stats['both_categories'] += 1
            elif 'computer science' in categories:
                stats['computer_science'] += 1
            elif 'biology' in categories:
                stats['biology'] += 1
            else:
                stats['uncategorized'] += 1
        
        return stats 