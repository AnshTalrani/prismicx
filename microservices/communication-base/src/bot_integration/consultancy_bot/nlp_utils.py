"""
NLP Utilities for Consultancy Bot

This module provides natural language processing utilities for the consultancy bot,
leveraging open source libraries like spaCy for entity extraction, sentiment analysis,
and key phrase extraction.
"""

import os
import re
from typing import Dict, Any, List, Tuple, Optional
import structlog
from collections import Counter

# Check if spaCy is available, otherwise use simpler implementations
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Check if transformers is available for sentiment analysis
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Configure logger
logger = structlog.get_logger(__name__)

class NLPProcessor:
    """
    NLP processor that provides text analysis capabilities using open source tools.
    Falls back to simpler implementations if libraries are not available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the NLP processor with configuration.
        
        Args:
            config: Bot configuration dictionary
        """
        self.config = config
        self.nlp = None
        self.sentiment_analyzer = None
        self.entity_types = config.get("entity_types", {})
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            try:
                # Try to load English model, or download if not present
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("Loaded spaCy model: en_core_web_sm")
                except OSError:
                    logger.warning("spaCy model not found, downloading en_core_web_sm")
                    spacy.cli.download("en_core_web_sm")
                    self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                logger.error(f"Failed to initialize spaCy: {str(e)}")
                self.nlp = None
        
        # Initialize sentiment analyzer if transformers available
        if TRANSFORMERS_AVAILABLE:
            try:
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                logger.info("Initialized sentiment analyzer using transformers")
            except Exception as e:
                logger.error(f"Failed to initialize sentiment analyzer: {str(e)}")
                self.sentiment_analyzer = None
                
        logger.info("NLP Processor initialized", 
                   spacy_available=SPACY_AVAILABLE,
                   transformers_available=TRANSFORMERS_AVAILABLE)
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text using NLP techniques to extract features.
        
        Args:
            text: The text to process
            
        Returns:
            Dictionary of extracted NLP features
        """
        # Define features we want to extract
        features = {}
        
        # Get NLP features configuration
        nlp_config = self.config.get("analysis_config", {}).get("nlp_features", {})
        required_features = nlp_config.get("required", [])
        
        # Extract entities
        if "entities" in required_features:
            features["entities"] = self.extract_entities(text)
        
        # Extract key phrases
        if "key_phrases" in required_features:
            features["key_phrases"] = self.extract_key_phrases(text)
        
        # Analyze sentiment
        if "sentiment" in required_features:
            features["sentiment"] = self.analyze_sentiment(text)
        
        # Measure text complexity
        if "complexity" in required_features or "complexity" in nlp_config.get("optional", []):
            features["complexity"] = self.measure_complexity(text)
        
        return features
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities from text.
        Uses spaCy if available, otherwise falls back to simple pattern matching.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of entity dictionaries with text and type
        """
        entities = []
        
        # Use spaCy for entity extraction if available
        if self.nlp is not None:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entities.append({"text": ent.text, "type": ent.label_})
                
                # If spaCy didn't find any entities of interest, fall back to custom extraction
                if not entities:
                    entities.extend(self._custom_entity_extraction(text))
                
                return entities
            except Exception as e:
                logger.error(f"Error in spaCy entity extraction: {str(e)}")
        
        # Fall back to custom entity extraction
        return self._custom_entity_extraction(text)
    
    def _custom_entity_extraction(self, text: str) -> List[Dict[str, str]]:
        """
        Custom entity extraction using pattern matching against entity dictionaries.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of entity dictionaries with text and type
        """
        entities = []
        text_lower = text.lower()
        
        # Check for entity types defined in config
        for entity_type, keywords in self.entity_types.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Look for the exact match with word boundaries
                    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                    if re.search(pattern, text_lower):
                        entities.append({"text": keyword, "type": entity_type})
        
        return entities
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of key phrases
        """
        # If spaCy is available, use noun chunks and entity detection
        if self.nlp is not None:
            try:
                doc = self.nlp(text)
                # Get noun phrases from the text
                noun_phrases = [chunk.text for chunk in doc.noun_chunks]
                
                # Get entities and add them to the key phrases
                entities = [ent.text for ent in doc.ents]
                
                # Combine and deduplicate
                all_phrases = list(set(noun_phrases + entities))
                
                # Filter out very short phrases and return
                return [phrase for phrase in all_phrases if len(phrase.split()) > 1]
            except Exception as e:
                logger.error(f"Error in key phrase extraction: {str(e)}")
        
        # Fall back to n-gram based extraction
        return self._extract_ngrams(text)
    
    def _extract_ngrams(self, text: str, n_range: Tuple[int, int] = (2, 3)) -> List[str]:
        """
        Extract n-grams from text as a simple key phrase extraction method.
        
        Args:
            text: The text to analyze
            n_range: Tuple of (min_n, max_n) for n-gram sizes
            
        Returns:
            List of n-grams that might be key phrases
        """
        words = re.findall(r'\b\w+\b', text.lower())
        ngrams = []
        
        for n in range(n_range[0], n_range[1] + 1):
            for i in range(len(words) - n + 1):
                ngrams.append(' '.join(words[i:i+n]))
        
        # Count occurrences and return most common
        counter = Counter(ngrams)
        return [ng for ng, count in counter.most_common(10)]
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text, returning a value from 0 (negative) to 1 (positive).
        
        Args:
            text: The text to analyze
            
        Returns:
            Sentiment score from 0 to 1
        """
        # Use transformers if available
        if self.sentiment_analyzer is not None:
            try:
                result = self.sentiment_analyzer(text)
                # Convert to 0-1 scale
                if result[0]["label"] == "POSITIVE":
                    return result[0]["score"]
                else:
                    return 1 - result[0]["score"]
            except Exception as e:
                logger.error(f"Error in transformer sentiment analysis: {str(e)}")
        
        # Fall back to lexicon-based analysis
        return self._lexicon_sentiment(text)
    
    def _lexicon_sentiment(self, text: str) -> float:
        """
        Simple lexicon-based sentiment analysis.
        
        Args:
            text: The text to analyze
            
        Returns:
            Sentiment score from 0 to 1
        """
        positive_words = [
            "good", "great", "excellent", "positive", "growth", "opportunity",
            "improve", "increase", "benefit", "advantage", "profit", "gain",
            "success", "successful", "effective", "efficient", "optimal", "best"
        ]
        
        negative_words = [
            "bad", "poor", "problem", "issue", "negative", "decline", "difficulty",
            "challenge", "risk", "threat", "loss", "decrease", "reduce", "fail",
            "failure", "ineffective", "inefficient", "worst", "liability"
        ]
        
        words = re.findall(r'\b\w+\b', text.lower())
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        return positive_count / (positive_count + negative_count)
    
    def measure_complexity(self, text: str) -> Dict[str, float]:
        """
        Measure the complexity of text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with complexity metrics
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Count words
        words = re.findall(r'\b\w+\b', text)
        
        # Calculate metrics
        avg_sentence_length = len(words) / max(1, len(sentences))
        avg_word_length = sum(len(word) for word in words) / max(1, len(words))
        
        # Calculate lexical diversity (unique words / total words)
        lexical_diversity = len(set(words)) / max(1, len(words))
        
        return {
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "lexical_diversity": lexical_diversity,
            "sentence_count": len(sentences),
            "word_count": len(words)
        }


# Singleton instance
nlp_processor = None

def get_nlp_processor(config: Dict[str, Any]) -> NLPProcessor:
    """
    Get the NLP processor instance, creating it if needed.
    
    Args:
        config: Bot configuration
        
    Returns:
        NLP processor instance
    """
    global nlp_processor
    if nlp_processor is None:
        nlp_processor = NLPProcessor(config)
    return nlp_processor 