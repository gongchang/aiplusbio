import os
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime
import re
from collections import Counter

class EventCategorizer:
    def __init__(self):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Define comprehensive category keywords with weights
        self.cs_keywords = {
            # Core CS terms (high weight)
            'computer science': 10, 'cs': 8, 'computing': 8, 'programming': 8,
            'software engineering': 8, 'algorithm': 8, 'data structure': 8,
            
            # AI/ML terms (high weight)
            'artificial intelligence': 10, 'ai': 8, 'machine learning': 10, 'ml': 8,
            'deep learning': 9, 'neural network': 9, 'neural networks': 9,
            'natural language processing': 9, 'nlp': 8, 'computer vision': 9,
            'robotics': 8, 'autonomous': 7, 'automation': 6,
            
            # Data Science terms
            'data science': 9, 'big data': 7, 'data mining': 7, 'data analysis': 6,
            'statistical learning': 8, 'predictive modeling': 7,
            
            # Systems and Infrastructure
            'distributed system': 8, 'distributed systems': 8, 'cloud computing': 7,
            'database': 7, 'databases': 7, 'system architecture': 7,
            'network': 6, 'networking': 6, 'cybersecurity': 8, 'security': 6,
            'blockchain': 7, 'cryptocurrency': 6, 'web development': 6,
            
            # Computational terms
            'computational': 7, 'optimization': 7, 'parallel computing': 8,
            'high performance computing': 8, 'hpc': 7, 'gpu': 6, 'cuda': 6,
            
            # Programming and Development
            'programming language': 7, 'software development': 7, 'code': 5,
            'debugging': 6, 'testing': 5, 'deployment': 5, 'api': 5,
            
            # Research areas
            'computer graphics': 8, 'virtual reality': 7, 'vr': 6, 'augmented reality': 7,
            'augmented reality': 7, 'human computer interaction': 8, 'hci': 7, 'information retrieval': 7,
            'search engine': 6, 'recommendation system': 7, 'social network': 6
        }
        
        self.biology_keywords = {
            # Core Biology terms (high weight)
            'biology': 10, 'biological': 8, 'biochemistry': 9, 'biotechnology': 8,
            'molecular biology': 10, 'cell biology': 9, 'microbiology': 8,
            'genetics': 9, 'genomics': 9, 'genome': 8, 'dna': 8, 'rna': 8,
            
            # Biomedical terms
            'biomedical': 8, 'medical': 6, 'medicine': 6, 'clinical': 6,
            'pharmaceutical': 7, 'drug discovery': 8, 'therapeutics': 7,
            'immunology': 8, 'immunotherapy': 8, 'vaccine': 7, 'antibody': 7,
            
            # Neuroscience terms
            'neuroscience': 9, 'neural': 7, 'brain': 6, 'cognitive': 6,
            'neurodegenerative': 8, 'alzheimer': 7, 'parkinson': 7,
            
            # Bioinformatics and Computational Biology
            'bioinformatics': 9, 'computational biology': 9, 'systems biology': 8,
            'protein': 7, 'proteomics': 8, 'transcriptomics': 8, 'metabolomics': 8,
            'pathway': 7, 'metabolism': 7, 'enzyme': 7, 'kinase': 7,
            
            # Evolution and Ecology
            'evolution': 8, 'evolutionary': 7, 'ecology': 7, 'ecological': 6,
            'species': 6, 'phylogeny': 7, 'phylogenetic': 7, 'biodiversity': 7,
            'conservation': 6, 'environmental': 5,
            
            # Modern Biology techniques
            'crispr': 8, 'gene editing': 8, 'synthetic biology': 8, 'synthetic': 6,
            'single cell': 7, 'single-cell': 7, 'sequencing': 7, 'next generation': 6,
            'ngs': 6, 'mass spectrometry': 7, 'microscopy': 6, 'imaging': 5,
            
            # Disease and Health
            'cancer': 7, 'oncology': 7, 'tumor': 6, 'disease': 5, 'pathology': 7,
            'infectious disease': 7, 'bacteria': 6, 'virus': 6, 'viral': 6,
            
            # Organisms and Systems
            'organism': 6, 'cell': 6, 'tissue': 6, 'organ': 5, 'stem cell': 7,
            'embryo': 6, 'growth': 5, 'reproduction': 6
        }
        
        # Define exclusion patterns (terms that might cause false positives)
        self.cs_exclusions = [
            'biological computing', 'bio-computing', 'biological network',
            'biological system', 'biological data', 'biological information'
        ]
        
        self.bio_exclusions = [
            'computer virus', 'computer network', 'computer system',
            'artificial neural network', 'neural network algorithm',
            'software development', 'web development', 'system development'
        ]
        
        # Define context patterns that boost confidence
        self.cs_context_patterns = [
            r'\b(computer|computing|software|algorithm|programming)\s+(science|engineering|research|development)',
            r'\b(artificial intelligence|machine learning|deep learning)\s+(research|development|application)',
            r'\b(data science|data analysis|big data)\s+(project|research|application)'
        ]
        
        self.bio_context_patterns = [
            r'\b(biology|biological|biochemistry|genetics)\s+(research|study|analysis)',
            r'\b(molecular biology|cell biology|microbiology)\s+(research|study)',
            r'\b(bioinformatics|computational biology)\s+(research|analysis|tool)'
        ]
    
    def categorize_event(self, event: Dict[str, Any]) -> List[str]:
        """Categorize an event using sophisticated keyword and pattern analysis"""
        categories = []
        
        # Prepare text for analysis
        text_to_analyze = f"{event.get('title', '')} {event.get('description', '')}"
        
        # Get categorization scores
        cs_score, bio_score = self._calculate_categorization_scores(text_to_analyze)
        
        # Apply thresholds and exclusions
        cs_final_score = self._apply_exclusions_and_context(cs_score, text_to_analyze, 'cs')
        bio_final_score = self._apply_exclusions_and_context(bio_score, text_to_analyze, 'bio')
        
        # Determine categories based on scores
        if cs_final_score >= 2.5:  # Lowered threshold for CS classification
            categories.append('computer science')
        if bio_final_score >= 2.0:  # Lowered threshold for Biology classification
            categories.append('biology')
        
        return categories
    
    def _calculate_categorization_scores(self, text: str) -> Tuple[float, float]:
        """Calculate weighted scores for CS and Biology categories"""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        word_count = len(words)
        
        # Calculate CS score
        cs_score = 0
        for keyword, weight in self.cs_keywords.items():
            if keyword in text_lower:
                # Count occurrences
                occurrences = text_lower.count(keyword)
                # Apply weight and normalize by text length, but don't over-normalize
                cs_score += (weight * occurrences) / max(word_count * 0.1, 1)
        
        # Calculate Biology score
        bio_score = 0
        for keyword, weight in self.biology_keywords.items():
            if keyword in text_lower:
                # Count occurrences
                occurrences = text_lower.count(keyword)
                # Apply weight and normalize by text length, but don't over-normalize
                bio_score += (weight * occurrences) / max(word_count * 0.1, 1)
        
        return cs_score, bio_score
    
    def _apply_exclusions_and_context(self, score: float, text: str, category: str) -> float:
        """Apply exclusion patterns and context-based adjustments"""
        text_lower = text.lower()
        adjusted_score = score
        
        # Apply exclusions with more sophisticated logic
        if category == 'cs':
            for exclusion in self.cs_exclusions:
                if exclusion in text_lower:
                    adjusted_score *= 0.2  # Reduce score more significantly
        elif category == 'bio':
            for exclusion in self.bio_exclusions:
                if exclusion in text_lower:
                    adjusted_score *= 0.2  # Reduce score more significantly
            
            # Additional exclusion for computer virus context
            if 'computer virus' in text_lower or 'malware' in text_lower:
                adjusted_score *= 0.1  # Almost eliminate score for computer viruses
        
        # Apply context patterns (boost confidence)
        if category == 'cs':
            for pattern in self.cs_context_patterns:
                if re.search(pattern, text_lower):
                    adjusted_score *= 1.5  # Boost score
        elif category == 'bio':
            for pattern in self.bio_context_patterns:
                if re.search(pattern, text_lower):
                    adjusted_score *= 1.5  # Boost score
        
        return adjusted_score
    
    def categorize_with_keywords(self, text: str) -> List[str]:
        """Legacy method for backward compatibility"""
        return self.categorize_event({'title': '', 'description': text})
    
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
    
    def get_detailed_categorization_analysis(self, text: str) -> Dict[str, Any]:
        """Get detailed analysis of categorization for debugging"""
        cs_score, bio_score = self._calculate_categorization_scores(text)
        cs_final = self._apply_exclusions_and_context(cs_score, text, 'cs')
        bio_final = self._apply_exclusions_and_context(bio_score, text, 'bio')
        
        # Find matched keywords
        text_lower = text.lower()
        cs_matches = {k: v for k, v in self.cs_keywords.items() if k in text_lower}
        bio_matches = {k: v for k, v in self.biology_keywords.items() if k in text_lower}
        
        return {
            'text': text,
            'cs_raw_score': cs_score,
            'bio_raw_score': bio_score,
            'cs_final_score': cs_final,
            'bio_final_score': bio_final,
            'cs_matches': cs_matches,
            'bio_matches': bio_matches,
            'cs_threshold_met': cs_final >= 2.5,
            'bio_threshold_met': bio_final >= 2.0
        } 