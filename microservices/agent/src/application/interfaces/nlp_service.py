"""NLP service interface for natural language processing tasks."""
from typing import Dict, Any, Optional, List, Protocol, Tuple

class INLPService(Protocol):
    """Interface for NLP service."""
    
    async def detect_purpose(self, text: str) -> Optional[str]:
        """
        Analyze text to determine the request purpose.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected purpose ID or None if undetermined
        """
        ...
    
    async def detect_purpose_with_confidence(self, text: str) -> Tuple[Optional[str], float]:
        """
        Analyze text to determine purpose with confidence score.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (purpose_id, confidence) or (None, 0.0) if undetermined
        """
        ...

    async def enrich_request(self, 
                           text: str, 
                           data: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrich request data with NLP analysis.
        
        Args:
            text: Request text
            data: Existing request data
            context: Optional additional context
            
        Returns:
            Enriched data with NLP insights
        """
        ...
    
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
        ... 