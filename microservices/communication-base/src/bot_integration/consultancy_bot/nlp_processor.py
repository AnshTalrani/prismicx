"""
NLP Processor for Consultancy Bot.
Provides natural language processing capabilities including entity recognition,
sentiment analysis, topic extraction, and other NLP features.
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import structlog
from dataclasses import dataclass, field
import numpy as np
from collections import Counter

# Configure logger
logger = structlog.get_logger(__name__)

# Try to import optional dependencies
try:
    import spacy
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    
    # Download necessary NLTK resources
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    
    SPACY_AVAILABLE = True
    NLTK_AVAILABLE = True
    
    # Load spaCy model
    try:
        nlp = spacy.load("en_core_web_md")
        logger.info("Loaded spaCy model: en_core_web_md")
    except OSError:
        # Fallback to small model if medium not available
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.warning("Failed to load spaCy model, downloading en_core_web_sm")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
            
    STOP_WORDS = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
except ImportError:
    SPACY_AVAILABLE = False
    NLTK_AVAILABLE = False
    logger.warning("spaCy and/or NLTK not available. Using fallback NLP processing.")
    
    # Define minimal fallback implementations
    STOP_WORDS = set([
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
        "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
        "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
        "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
        "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
        "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
        "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", 
        "at", "by", "for", "with", "about", "against", "between", "into", "through", 
        "during", "before", "after", "above", "below", "to", "from", "up", "down", 
        "in", "out", "on", "off", "over", "under", "again", "further", "then", 
        "once", "here", "there", "when", "where", "why", "how", "all", "any", 
        "both", "each", "few", "more", "most", "other", "some", "such", "no", 
        "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", 
        "t", "can", "will", "just", "don", "don't", "should", "should've", "now", 
        "d", "ll", "m", "o", "re", "ve", "y", "ain", "aren", "aren't", "couldn", 
        "couldn't", "didn", "didn't", "doesn", "doesn't", "hadn", "hadn't", "hasn", 
        "hasn't", "haven", "haven't", "isn", "isn't", "ma", "mightn", "mightn't", 
        "mustn", "mustn't", "needn", "needn't", "shan", "shan't", "shouldn", 
        "shouldn't", "wasn", "wasn't", "weren", "weren't", "won", "won't", "wouldn", 
        "wouldn't"
    ])

# Domain-specific terms for business consultancy
BUSINESS_TERMS = {
    "strategy": ["strategic", "plan", "roadmap", "vision", "mission", "goal", "objective"],
    "finance": ["revenue", "profit", "cost", "budget", "funding", "investment", "roi", "cash flow"],
    "marketing": ["brand", "campaign", "market", "customer", "segment", "positioning", "promotion"],
    "operations": ["process", "efficiency", "optimization", "workflow", "supply chain", "logistics"],
    "hr": ["talent", "recruitment", "hiring", "employee", "retention", "performance", "compensation"],
    "legal": ["compliance", "regulation", "contract", "terms", "agreement", "patent", "copyright"],
    "technology": ["digital", "transformation", "automation", "ai", "machine learning", "cloud", "saas"],
    "risk": ["mitigation", "assessment", "management", "contingency", "hazard", "threat", "vulnerability"]
}

@dataclass
class NLPFeatures:
    """Container for extracted NLP features from text"""
    entities: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    domain_terms: Dict[str, List[str]] = field(default_factory=dict)
    complexity: Dict[str, Any] = field(default_factory=dict)
    urgency: float = 0.0
    formality: float = 0.0
    request_type: str = ""
    raw_features: Dict[str, Any] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "entities": self.entities,
            "sentiment": self.sentiment,
            "keywords": self.keywords,
            "topics": self.topics,
            "domain_terms": self.domain_terms,
            "complexity": self.complexity,
            "urgency": self.urgency,
            "formality": self.formality,
            "request_type": self.request_type
        }
    
    def get_entity_text(self, entity_type: str) -> List[str]:
        """Get text of entities of a specific type"""
        return [e["text"] for e in self.entities if e["type"] == entity_type]
    
    def get_domain_keywords(self) -> List[str]:
        """Get all domain-specific keywords found"""
        result = []
        for domain, terms in self.domain_terms.items():
            result.extend(terms)
        return result

class NLPProcessor:
    """Natural Language Processing capabilities for consultancy bot"""
    
    def __init__(self, use_spacy: bool = True, use_nltk: bool = True):
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        self.use_nltk = use_nltk and NLTK_AVAILABLE
        
        # Load urgency terms
        self.urgency_terms = {
            "high": ["urgent", "immediately", "asap", "critical", "emergency", "now", "rushing",
                    "deadline", "quickly", "expedite", "important", "priority", "fast"],
            "medium": ["soon", "shortly", "today", "tomorrow", "next week", "need", "require", 
                      "should", "would like", "waiting", "pending"],
            "low": ["sometime", "when you can", "eventually", "in the future", "no rush", 
                   "take your time", "wondering", "curious", "interested"]
        }
        
        # Load formality markers
        self.formality_markers = {
            "formal": ["please", "kindly", "would you", "could you", "may I", "thank you", 
                      "appreciate", "sincerely", "regards", "respectfully", "formally", 
                      "officially", "pursuant", "accordingly", "hereafter"],
            "informal": ["hey", "hi", "hello", "btw", "by the way", "thanks", "cool", "awesome", 
                        "great", "ok", "okay", "yeah", "yep", "nope", "sure", "cheers", "later"]
        }
        
        # Request type patterns
        self.request_patterns = {
            "question": [r"\?$", r"^(what|who|when|where|why|how|is|are|can|could|would|will|should)"],
            "instruction": [r"^(please|kindly)?\s*(do|make|create|generate|implement|execute|run|build|set up|configure|install|deploy)"],
            "information": [r"^(fyi|for your information|note that|be advised|please note|heads up|just to let you know)"],
            "clarification": [r"(i meant|to clarify|to be clear|what i mean is|in other words|let me explain|to elaborate)"]
        }
        
        logger.info("NLP Processor initialized", 
                   spacy_available=self.use_spacy, 
                   nltk_available=self.use_nltk)
    
    def process_text(self, text: str) -> NLPFeatures:
        """Process text and extract NLP features"""
        features = NLPFeatures()
        
        if not text or not isinstance(text, str):
            logger.warning("Invalid input to NLP processor", text_type=type(text))
            return features
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Use spaCy for advanced NLP if available
        if self.use_spacy:
            doc = nlp(cleaned_text)
            
            # Extract entities
            features.entities = [
                {"text": ent.text, "type": ent.label_, "start": ent.start_char, "end": ent.end_char}
                for ent in doc.ents
            ]
            
            # Extract keywords using noun chunks and proper nouns
            keywords = list(set([chunk.text.lower() for chunk in doc.noun_chunks] + 
                               [token.text.lower() for token in doc if token.pos_ == "PROPN"]))
            features.keywords = [k for k in keywords if k not in STOP_WORDS and len(k) > 1]
            
            # Basic sentiment analysis
            features.sentiment = self._analyze_sentiment_spacy(doc)
            
            # Text complexity
            features.complexity = self._analyze_complexity(doc)
            
            # Store raw features for advanced usage
            features.raw_features["spacy_doc"] = doc
            
        # Fall back to or supplement with NLTK processing
        elif self.use_nltk:
            # Tokenize and extract keywords
            tokens = word_tokenize(cleaned_text)
            lemmatized_tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens]
            features.keywords = [token for token in lemmatized_tokens 
                              if token not in STOP_WORDS and len(token) > 1]
            
            # Basic sentiment analysis
            features.sentiment = self._analyze_sentiment_nltk(cleaned_text)
            
        # Use simple fallback methods if neither spaCy nor NLTK is available
        else:
            # Simple word extraction
            words = cleaned_text.lower().split()
            features.keywords = [word for word in words if word not in STOP_WORDS and len(word) > 1]
            
            # Simple sentiment analysis
            features.sentiment = self._analyze_sentiment_simple(cleaned_text)
        
        # Domain-specific term extraction (works with any NLP backend)
        features.domain_terms = self._extract_domain_terms(cleaned_text)
        
        # Extract topics from domain terms
        if features.domain_terms:
            features.topics = list(features.domain_terms.keys())
        
        # Analyze urgency
        features.urgency = self._analyze_urgency(cleaned_text)
        
        # Analyze formality
        features.formality = self._analyze_formality(cleaned_text)
        
        # Determine request type
        features.request_type = self._determine_request_type(cleaned_text)
        
        logger.debug("NLP features extracted", 
                    entities_count=len(features.entities),
                    keywords_count=len(features.keywords),
                    topics=features.topics,
                    sentiment=features.sentiment,
                    urgency=features.urgency,
                    request_type=features.request_type)
        
        return features
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        # Convert to lowercase and strip whitespace
        text = text.strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s\.\,\?\!\:\;\-\']', ' ', text)
        
        return text
    
    def _analyze_sentiment_spacy(self, doc) -> Dict[str, Any]:
        """Analyze sentiment using spaCy"""
        # Simple rule-based sentiment analysis
        # A more sophisticated approach would use a dedicated sentiment model
        
        # Count positive and negative words
        positive_terms = ["good", "great", "excellent", "positive", "happy", "pleased", 
                         "satisfied", "beneficial", "success", "successful", "well", "nice"]
        negative_terms = ["bad", "poor", "terrible", "negative", "unhappy", "disappointed", 
                         "dissatisfied", "harmful", "failure", "poorly", "problem", "issue"]
        
        pos_count = sum(1 for token in doc if token.lemma_.lower() in positive_terms)
        neg_count = sum(1 for token in doc if token.lemma_.lower() in negative_terms)
        
        # Check for negations that might flip sentiment
        negations = ["not", "no", "never", "neither", "nor", "cannot", "can't", "won't", "wouldn't"]
        negation_count = sum(1 for token in doc if token.lemma_.lower() in negations)
        
        # Adjust for negations (simplistic approach)
        if negation_count > 0:
            pos_count, neg_count = neg_count, pos_count
        
        # Calculate polarity score (-1 to 1)
        total = pos_count + neg_count
        if total > 0:
            polarity = (pos_count - neg_count) / total
        else:
            polarity = 0.0
            
        return {
            "polarity": polarity,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "negation_count": negation_count,
            "assessment": "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"
        }
    
    def _analyze_sentiment_nltk(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using NLTK"""
        # Simple NLTK-based sentiment analysis
        tokens = word_tokenize(text.lower())
        
        # Count positive and negative words
        positive_terms = ["good", "great", "excellent", "positive", "happy", "pleased", 
                         "satisfied", "beneficial", "success", "successful", "well", "nice"]
        negative_terms = ["bad", "poor", "terrible", "negative", "unhappy", "disappointed", 
                         "dissatisfied", "harmful", "failure", "poorly", "problem", "issue"]
        
        pos_count = sum(1 for token in tokens if token in positive_terms)
        neg_count = sum(1 for token in tokens if token in negative_terms)
        
        # Check for negations
        negations = ["not", "no", "never", "neither", "nor", "cannot", "can't", "won't", "wouldn't"]
        negation_count = sum(1 for token in tokens if token in negations)
        
        # Adjust for negations (simplistic approach)
        if negation_count > 0:
            pos_count, neg_count = neg_count, pos_count
        
        # Calculate polarity score (-1 to 1)
        total = pos_count + neg_count
        if total > 0:
            polarity = (pos_count - neg_count) / total
        else:
            polarity = 0.0
            
        return {
            "polarity": polarity,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "negation_count": negation_count,
            "assessment": "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"
        }
    
    def _analyze_sentiment_simple(self, text: str) -> Dict[str, Any]:
        """Simple fallback sentiment analysis"""
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_terms = ["good", "great", "excellent", "positive", "happy", "pleased", 
                         "satisfied", "beneficial", "success", "successful", "well", "nice"]
        negative_terms = ["bad", "poor", "terrible", "negative", "unhappy", "disappointed", 
                         "dissatisfied", "harmful", "failure", "poorly", "problem", "issue"]
        
        pos_count = sum(1 for term in positive_terms if term in text_lower)
        neg_count = sum(1 for term in negative_terms if term in text_lower)
        
        # Check for negations
        negations = ["not", "no", "never", "neither", "nor", "cannot", "can't", "won't", "wouldn't"]
        negation_count = sum(1 for term in negations if term in text_lower)
        
        # Calculate polarity score (-1 to 1)
        total = pos_count + neg_count
        if total > 0:
            polarity = (pos_count - neg_count) / total
        else:
            polarity = 0.0
            
        return {
            "polarity": polarity,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "negation_count": negation_count,
            "assessment": "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"
        }
    
    def _extract_domain_terms(self, text: str) -> Dict[str, List[str]]:
        """Extract domain-specific terminology"""
        text_lower = text.lower()
        result = {}
        
        for domain, terms in BUSINESS_TERMS.items():
            found_terms = []
            for term in terms:
                if term in text_lower:
                    found_terms.append(term)
            
            if found_terms:
                result[domain] = found_terms
                
        return result
    
    def _analyze_complexity(self, doc) -> Dict[str, Any]:
        """Analyze text complexity"""
        # Count sentences, words and syllables
        sentences = list(doc.sents)
        sentence_count = len(sentences)
        word_count = len([token for token in doc if not token.is_punct])
        
        if sentence_count == 0:
            return {
                "readability": "unknown",
                "avg_sentence_length": 0,
                "avg_word_length": 0
            }
        
        # Calculate average sentence length
        avg_sentence_length = word_count / sentence_count
        
        # Calculate average word length
        avg_word_length = sum(len(token.text) for token in doc if not token.is_punct) / max(1, word_count)
        
        # Simple readability assessment
        if avg_sentence_length > 25 or avg_word_length > 6:
            readability = "complex"
        elif avg_sentence_length > 15 or avg_word_length > 5:
            readability = "moderate"
        else:
            readability = "simple"
            
        return {
            "readability": readability,
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length
        }
    
    def _analyze_urgency(self, text: str) -> float:
        """Analyze perceived urgency in the text (0.0 to 1.0)"""
        text_lower = text.lower()
        
        # Count urgency terms by category
        high_count = sum(1 for term in self.urgency_terms["high"] if term in text_lower)
        medium_count = sum(1 for term in self.urgency_terms["medium"] if term in text_lower)
        low_count = sum(1 for term in self.urgency_terms["low"] if term in text_lower)
        
        # Weight the counts
        weighted_score = (high_count * 1.0 + medium_count * 0.5 + low_count * 0.2)
        max_possible = max(1, high_count + medium_count + low_count)  # Avoid division by zero
        
        # Normalize to 0-1 scale
        urgency = min(1.0, weighted_score / max_possible)
        
        return urgency
    
    def _analyze_formality(self, text: str) -> float:
        """Analyze formality level in the text (0.0 to 1.0, where 1.0 is most formal)"""
        text_lower = text.lower()
        
        # Count formality markers
        formal_count = sum(1 for term in self.formality_markers["formal"] if term in text_lower)
        informal_count = sum(1 for term in self.formality_markers["informal"] if term in text_lower)
        
        # Weight and normalize
        total = formal_count + informal_count
        if total == 0:
            # Default to mid-formality if no markers detected
            return 0.5
            
        formality = formal_count / total
        
        return formality
    
    def _determine_request_type(self, text: str) -> str:
        """Determine the type of request being made"""
        # Check each pattern type
        for req_type, patterns in self.request_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text.lower()):
                    return req_type
        
        # Default to general request if no pattern matches
        return "general"
    
    def get_dominant_topics(self, features: NLPFeatures, top_n: int = 3) -> List[str]:
        """Get the most dominant topics from extracted features"""
        if not features.domain_terms:
            return []
        
        # Count terms by domain
        domain_counts = {domain: len(terms) for domain, terms in features.domain_terms.items()}
        
        # Sort domains by term count and return top N
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [domain for domain, count in sorted_domains[:top_n]]
    
    def get_similar_features(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0.0 to 1.0)"""
        if not self.use_spacy:
            return 0.0  # Similarity requires spaCy
        
        # Process both texts
        doc1 = nlp(self._clean_text(text1))
        doc2 = nlp(self._clean_text(text2))
        
        # Return cosine similarity
        return doc1.similarity(doc2)
    
    def extract_action_items(self, text: str) -> List[str]:
        """Extract potential action items from text"""
        action_items = []
        
        # Use spaCy if available
        if self.use_spacy:
            doc = nlp(text)
            
            # Look for imperative verbs and action patterns
            for sent in doc.sents:
                # Check if sentence starts with a verb
                if sent[0].pos_ == "VERB":
                    action_items.append(sent.text)
                
                # Check for modal verbs followed by action verbs
                for i, token in enumerate(sent):
                    if token.text.lower() in ["should", "must", "need", "have to"]:
                        if i+1 < len(sent) and sent[i+1].pos_ in ["VERB", "AUX"]:
                            action_items.append(sent.text)
                            break
        
        # Simple fallback method
        else:
            sentences = re.split(r'[.!?]', text)
            action_verbs = ["create", "make", "do", "implement", "prepare", "develop", 
                           "build", "establish", "ensure", "provide", "send", "review"]
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Check if sentence starts with an action verb
                first_word = sentence.split()[0].lower() if sentence.split() else ""
                if first_word in action_verbs:
                    action_items.append(sentence)
                
                # Check for modal + action patterns
                words = sentence.lower().split()
                for i, word in enumerate(words):
                    if word in ["should", "must", "need", "have to"]:
                        if i+1 < len(words) and words[i+1] in action_verbs:
                            action_items.append(sentence)
                            break
        
        return action_items

def get_nlp_processor() -> NLPProcessor:
    """Factory function to get an NLP processor instance"""
    return NLPProcessor(use_spacy=SPACY_AVAILABLE, use_nltk=NLTK_AVAILABLE) 