"""
Simple purpose detection service using keyword matching with spaCy enhancement.
"""
import json
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
import re

# Import spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from src.application.interfaces.nlp_service import INLPService
from src.domain.entities.purpose import Purpose
from microservices.agent.src.application.interfaces.repository.purpose_repository import IPurposeRepository

logger = logging.getLogger(__name__)

class DefaultNLPService(INLPService):
    """
    NLP service that uses spaCy for enhanced purpose detection.
    Falls back to simple keyword matching if spaCy is not available.
    Uses lemmatization and linguistic features to improve matching accuracy.
    """
    
    def __init__(self, purpose_repository: IPurposeRepository):
        """
        Initialize DefaultNLPService.
        
        Args:
            purpose_repository: Repository for accessing purpose definitions
        """
        self.logger = logging.getLogger(__name__)
        self.purpose_repository = purpose_repository
        self._purpose_keywords = {}  # Cache for purpose keywords
        
        # Initialize spaCy if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("Initialized spaCy model for NLP processing")
            except OSError:
                self.logger.warning("Could not load spaCy model. Run 'python -m spacy download en_core_web_sm' to install it")
        else:
            self.logger.warning("spaCy not available. Install with 'pip install spacy' for enhanced NLP capabilities")
        
        self._initialize_keywords()
    
    async def _initialize_keywords(self):
        """Initialize purpose keywords from repository."""
        purposes = await self.purpose_repository.list_purposes()
        for purpose in purposes:
            if purpose.keywords:
                self._purpose_keywords[purpose.id] = purpose.keywords
    
    async def detect_purpose(self, text: str) -> Optional[str]:
        """
        Analyze text to determine the request purpose.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected purpose ID or None if undetermined
        """
        purpose_id, _ = await self.detect_purpose_with_confidence(text)
        return purpose_id
    
    async def detect_purpose_with_confidence(self, text: str) -> Tuple[Optional[str], float]:
        """
        Analyze text to determine purpose with confidence score.
        Uses spaCy for enhanced matching if available.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (purpose_id, confidence) or (None, 0.0) if undetermined
        """
        if not text:
            return None, 0.0
        
        # Refresh keywords if cache is empty
        if not self._purpose_keywords:
            await self._initialize_keywords()
        
        # Use spaCy if available
        if self.nlp is not None:
            return self._detect_purpose_with_spacy(text)
        else:
            # Fallback to simple keyword matching
            return self._detect_purpose_with_simple_matching(text)
    
    def _detect_purpose_with_spacy(self, text: str) -> Tuple[Optional[str], float]:
        """
        Detect purpose using spaCy for enhanced linguistic analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (purpose_id, confidence)
        """
        doc = self.nlp(text.lower())
        
        # Extract lemmas, removing stop words and punctuation
        text_lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        text_lemmas_set = set(text_lemmas)
        
        best_match = None
        best_score = 0.0
        
        for purpose_id, keywords in self._purpose_keywords.items():
            current_score = self._calculate_spacy_match(text, text_lemmas_set, keywords)
            if current_score > best_score:
                best_score = current_score
                best_match = purpose_id
        
        # Return None if confidence below threshold
        if best_score < 0.3:
            self.logger.debug(f"No purpose detected with sufficient confidence for: {text}")
            return None, 0.0
            
        self.logger.info(f"Detected purpose {best_match} with confidence {best_score} for text: {text}")
        return best_match, best_score
    
    def _calculate_spacy_match(self, original_text: str, text_lemmas_set: set, keywords: List[str]) -> float:
        """
        Calculate match score using spaCy lemmatization.
        
        Args:
            original_text: Original text for exact matching
            text_lemmas_set: Set of lemmas from the text
            keywords: List of keywords to match
            
        Returns:
            Match score between 0.0 and 1.0
        """
        matches = 0
        importance_sum = 0
        total_importance = 0
        
        for kw in keywords:
            # Split keyword by : to get importance
            parts = kw.split(':')
            if len(parts) > 1:
                keyword = parts[0].strip()
                importance = float(parts[1])
            else:
                keyword = kw.strip()
                importance = 1.0
            
            total_importance += importance
            
            # Process keyword with spaCy
            kw_doc = self.nlp(keyword.lower())
            
            # Extract keyword lemmas
            keyword_lemmas = [token.lemma_ for token in kw_doc if not token.is_stop and not token.is_punct]
            
            # Check for exact match first (higher confidence)
            if keyword.lower() in original_text.lower():
                matches += 1
                importance_sum += importance
                continue
                
            # Check for lemma matches
            lemma_matches = 0
            for lemma in keyword_lemmas:
                if lemma in text_lemmas_set:
                    lemma_matches += 1
            
            # If all lemmas matched, count as a match with slightly lower weight
            if lemma_matches > 0 and len(keyword_lemmas) > 0 and lemma_matches == len(keyword_lemmas):
                matches += 0.8  # Slight penalty for not being exact match
                importance_sum += importance * 0.8
        
        if not keywords or total_importance == 0:
            return 0.0
            
        # Calculate weighted score
        return importance_sum / (total_importance * 2)
    
    def _detect_purpose_with_simple_matching(self, text: str) -> Tuple[Optional[str], float]:
        """
        Fallback method that uses simple keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (purpose_id, confidence)
        """
        normalized_text = text.lower()
        best_match = None
        best_score = 0.0
        
        # Simple keyword matching algorithm
        for purpose_id, keywords in self._purpose_keywords.items():
            current_score = self._calculate_keyword_match(normalized_text, keywords)
            if current_score > best_score:
                best_score = current_score
                best_match = purpose_id
        
        # Return None if confidence below threshold
        if best_score < 0.3:
            self.logger.debug(f"No purpose detected with sufficient confidence for: {text}")
            return None, 0.0
            
        self.logger.info(f"Detected purpose {best_match} with confidence {best_score} for text: {text}")
        return best_match, best_score
    
    def _calculate_keyword_match(self, text: str, keywords: List[str]) -> float:
        """
        Calculate keyword match score.
        
        Args:
            text: Normalized text to analyze
            keywords: List of keywords to match
            
        Returns:
            Match score between 0.0 and 1.0
        """
        matches = 0
        importance_sum = 0
        
        for kw in keywords:
            # Split keyword by : to get importance
            parts = kw.split(':')
            if len(parts) > 1:
                keyword = parts[0]
                importance = float(parts[1])
            else:
                keyword = kw
                importance = 1.0
                
            if keyword in text:
                matches += 1
                importance_sum += importance
        
        if not keywords:
            return 0.0
            
        # Calculate weighted score
        return importance_sum / (sum([1.0 for _ in keywords]) * 2)
    
    async def enrich_request(self, 
                           text: str, 
                           data: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Legacy method - only kept for compatibility.
        Now only adds purpose_id if detected.
        
        Args:
            text: Request text
            data: Existing request data
            context: Optional additional context
            
        Returns:
            Data with purpose_id if detected
        """
        enriched_data = data.copy()
        
        # Only try to detect purpose if not already set
        if 'purpose_id' not in enriched_data:
            purpose_id = await self.detect_purpose(text)
            if purpose_id:
                enriched_data['purpose_id'] = purpose_id
        
        return enriched_data
    
    async def classify_text(self, 
                          text: str, 
                          categories: List[str],
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Classify text into predefined categories.
        
        Args:
            text: Text to classify
            categories: Available categories
            context: Optional additional context
            
        Returns:
            Dictionary of {category: confidence_score}
        """
        # If spaCy is available, use it for better classification
        if self.nlp is not None:
            doc = self.nlp(text.lower())
            
            # Extract lemmas for analysis
            text_lemmas = set([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])
            
            # Use a simple scoring mechanism - could be improved in future versions
            results = {}
            for category in categories:
                # Process category with spaCy
                cat_doc = self.nlp(category.lower())
                cat_lemmas = set([token.lemma_ for token in cat_doc if not token.is_stop and not token.is_punct])
                
                # Calculate similarity score
                if len(cat_lemmas) > 0:
                    common_lemmas = text_lemmas.intersection(cat_lemmas)
                    score = len(common_lemmas) / len(cat_lemmas) * 0.5
                    results[category] = min(max(score, 0.1), 0.9)  # Clamp between 0.1 and 0.9
                else:
                    results[category] = 0.1
                    
            return results
        else:
            self.logger.warning("classify_text works better with spaCy installed")
            # Return default low confidence for all categories
            return {category: 0.1 for category in categories} 