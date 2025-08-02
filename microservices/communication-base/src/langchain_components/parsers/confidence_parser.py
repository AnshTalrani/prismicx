"""
Confidence-aware parser for evaluating model certainty in responses.

This module provides a parser that evaluates model confidence levels in responses,
extracts uncertainty indicators, and can trigger additional processing or research
for low-confidence answers.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Set

from langchain.output_parsers import PydanticOutputParser
from langchain.schema import OutputParserException
from pydantic import BaseModel, Field

class ConfidenceMetrics(BaseModel):
    """
    Confidence metrics for a model response.
    """
    
    overall_confidence: float = Field(
        ...,
        description="Overall confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    uncertain_segments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Segments with uncertainty indicators"
    )
    
    requires_verification: bool = Field(
        False,
        description="Whether the response requires additional verification"
    )
    
    reasoning: str = Field(
        "",
        description="Reasoning behind confidence assessment"
    )
    
    factual_consistency: float = Field(
        1.0,
        description="Consistency with known facts (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

class ConfidenceParser:
    """
    Confidence-aware parser for evaluating model certainty in responses.
    
    This class analyzes responses to detect uncertainty indicators, evaluates
    confidence levels in different segments, and can trigger additional processing
    for low-confidence answers.
    """
    
    def __init__(
        self,
        llm: Any = None,
        confidence_threshold: float = 0.7,
        verification_threshold: float = 0.5,
        config_integration: Any = None,
        bot_type: Optional[str] = None
    ):
        """
        Initialize confidence parser.
        
        Args:
            llm: LLM for confidence evaluation
            confidence_threshold: Threshold for acceptable confidence
            verification_threshold: Threshold below which verification is needed
            config_integration: Integration with the config system
            bot_type: Type of bot for configuration lookup
        """
        self.llm = llm
        self.confidence_threshold = confidence_threshold
        self.verification_threshold = verification_threshold
        self.config_integration = config_integration
        self.bot_type = bot_type
        self.logger = logging.getLogger(__name__)
        
        # Load bot-specific configuration if available
        if config_integration and bot_type:
            self._load_config_settings()
        
        # Initialize uncertainty patterns
        self._init_uncertainty_patterns()
        
        # Pydantic parser for metrics
        self.metrics_parser = PydanticOutputParser(pydantic_object=ConfidenceMetrics)
    
    def _load_config_settings(self) -> None:
        """
        Load parser settings from bot configuration.
        """
        try:
            config = self.config_integration.get_config(self.bot_type)
            parser_config = config.get("parsers", {}).get("confidence_parser", {})
            
            if "confidence_threshold" in parser_config:
                self.confidence_threshold = parser_config["confidence_threshold"]
            
            if "verification_threshold" in parser_config:
                self.verification_threshold = parser_config["verification_threshold"]
                
        except Exception as e:
            self.logger.warning(f"Failed to load confidence parser config: {e}")
    
    def _init_uncertainty_patterns(self) -> None:
        """
        Initialize patterns for detecting uncertainty.
        """
        # Common uncertainty phrases
        self.uncertainty_phrases = [
            r"\bI'm not sure\b",
            r"\bI don't know\b",
            r"\bI believe\b",
            r"\bprobably\b",
            r"\bmight\b",
            r"\bcould be\b",
            r"\bperhaps\b",
            r"\bpossibly\b",
            r"\buncertain\b",
            r"\bunclear\b",
            r"\bI think\b",
            r"\bseem[s]? to\b",
            r"\bappear[s]? to\b",
            r"\blikely\b",
            r"\btends to\b",
            r"\bgenerally\b",
            r"\btypically\b",
            r"\busually\b",
            r"\bmay\b",
            r"\bmaybe\b"
        ]
        
        # Hedge phrases suggesting uncertainty
        self.hedge_phrases = [
            r"\bsomewhat\b",
            r"\bto some extent\b",
            r"\bto a certain degree\b",
            r"\bin most cases\b",
            r"\bin general\b",
            r"\boften\b",
            r"\bfrequently\b",
            r"\boccasionally\b",
            r"\broughly\b",
            r"\bapproximately\b",
            r"\baround\b",
            r"\babout\b"
        ]
        
        # Knowledge disclaimers
        self.knowledge_disclaimers = [
            r"\bbased on my knowledge\b",
            r"\bas of my last update\b",
            r"\bas far as I know\b",
            r"\bto the best of my knowledge\b",
            r"\bmy information might be outdated\b",
            r"\bI don't have access to\b",
            r"\bI don't have information on\b",
            r"\bwithout more context\b",
            r"\bwithout more information\b"
        ]
        
        # Compile all patterns for efficiency
        all_patterns = (
            self.uncertainty_phrases +
            self.hedge_phrases +
            self.knowledge_disclaimers
        )
        self.uncertainty_pattern = re.compile("|".join(all_patterns), re.IGNORECASE)
    
    def analyze_confidence(self, response: str) -> ConfidenceMetrics:
        """
        Analyze confidence in a response.
        
        Args:
            response: Model response text
            
        Returns:
            ConfidenceMetrics with confidence assessment
            
        Raises:
            OutputParserException: If confidence analysis fails
        """
        # If LLM is provided, use it for confidence assessment
        if self.llm:
            try:
                return self._llm_based_confidence(response)
            except Exception as e:
                self.logger.warning(f"LLM-based confidence analysis failed: {e}")
                # Fall back to rule-based assessment
        
        # Use rule-based assessment
        return self._rule_based_confidence(response)
    
    def _llm_based_confidence(self, response: str) -> ConfidenceMetrics:
        """
        Use LLM to assess confidence in a response.
        
        Args:
            response: Model response text
            
        Returns:
            ConfidenceMetrics with confidence assessment
        """
        prompt = f"""
        Analyze the following AI response for signs of uncertainty, confidence level, and factual consistency.
        
        Response to analyze:
        ```
        {response}
        ```
        
        Evaluate with the following criteria:
        1. Overall confidence level (0.0-1.0)
        2. Identify specific segments expressing uncertainty
        3. Determine if the response needs verification
        4. Provide brief reasoning for your assessment
        5. Assess factual consistency (0.0-1.0)
        
        Return your analysis as a JSON object with these fields:
        - overall_confidence: float between 0.0 and 1.0
        - uncertain_segments: list of objects with "text" and "confidence" fields
        - requires_verification: boolean
        - reasoning: string explaining your assessment
        - factual_consistency: float between 0.0 and 1.0
        
        Only return the JSON object, nothing else.
        """
        
        result = self.llm.predict(prompt)
        
        try:
            # Extract JSON from result
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                metrics_dict = json.loads(json_str)
                return ConfidenceMetrics(**metrics_dict)
            else:
                raise ValueError("No JSON found in LLM response")
                
        except (ValueError, json.JSONDecodeError) as e:
            raise OutputParserException(f"Failed to parse LLM confidence assessment: {e}")
    
    def _rule_based_confidence(self, response: str) -> ConfidenceMetrics:
        """
        Use rule-based approach to assess confidence in a response.
        
        Args:
            response: Model response text
            
        Returns:
            ConfidenceMetrics with confidence assessment
        """
        # Find all uncertainty indicators
        matches = list(self.uncertainty_pattern.finditer(response))
        
        # Extract uncertain segments
        uncertain_segments = []
        for match in matches:
            # Extract context around the match (up to 100 chars)
            start = max(0, match.start() - 50)
            end = min(len(response), match.end() + 50)
            context = response[start:end]
            
            # Determine confidence for this segment (inversely related to strength of uncertainty)
            confidence = 0.5  # Default moderate confidence
            
            # Adjust based on type of uncertainty
            phrase = match.group(0).lower()
            
            # Strong uncertainty indicators reduce confidence more
            if any(re.search(p, phrase, re.IGNORECASE) for p in [
                r"I don't know",
                r"I'm not sure",
                r"uncertain",
                r"unclear"
            ]):
                confidence = 0.3
            # Moderate uncertainty
            elif any(re.search(p, phrase, re.IGNORECASE) for p in [
                r"probably",
                r"might",
                r"could be",
                r"perhaps"
            ]):
                confidence = 0.5
            # Mild uncertainty
            else:
                confidence = 0.7
                
            uncertain_segments.append({
                "text": context,
                "indicator": match.group(0),
                "confidence": confidence
            })
        
        # Calculate overall confidence
        if not uncertain_segments:
            overall_confidence = 1.0
        else:
            # Weight by segment length
            total_uncertainty_chars = sum(len(segment["text"]) for segment in uncertain_segments)
            response_length = len(response)
            
            # Base confidence on ratio of uncertain text to total text
            uncertainty_ratio = min(1.0, total_uncertainty_chars / response_length)
            
            # Calculate average confidence of uncertain segments
            avg_segment_confidence = sum(segment["confidence"] for segment in uncertain_segments) / len(uncertain_segments)
            
            # Combine metrics: higher ratio of uncertain text reduces confidence more
            overall_confidence = 1.0 - (uncertainty_ratio * (1.0 - avg_segment_confidence))
        
        # Determine if verification is needed
        requires_verification = overall_confidence < self.verification_threshold
        
        # Create reasoning
        if uncertain_segments:
            reasoning = f"Found {len(uncertain_segments)} uncertainty indicators."
        else:
            reasoning = "No explicit uncertainty indicators found."
        
        return ConfidenceMetrics(
            overall_confidence=overall_confidence,
            uncertain_segments=uncertain_segments,
            requires_verification=requires_verification,
            reasoning=reasoning,
            factual_consistency=overall_confidence  # Simplification for rule-based approach
        )
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """
        Process a response with confidence analysis.
        
        Args:
            response: Model response text
            
        Returns:
            Dictionary with processed response and confidence metrics
        """
        try:
            # Analyze confidence
            confidence_metrics = self.analyze_confidence(response)
            
            result = {
                "original_response": response,
                "confidence_metrics": confidence_metrics.dict(),
                "confidence_level": self._get_confidence_level(confidence_metrics.overall_confidence),
                "meets_threshold": confidence_metrics.overall_confidence >= self.confidence_threshold
            }
            
            # Add verification suggestion if needed
            if confidence_metrics.requires_verification:
                result["verification_needed"] = True
                result["uncertain_topics"] = self._extract_uncertain_topics(confidence_metrics.uncertain_segments)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing response confidence: {e}", exc_info=True)
            # Return basic result if analysis fails
            return {
                "original_response": response,
                "confidence_metrics": {"overall_confidence": 0.5},
                "confidence_level": "MEDIUM",
                "meets_threshold": False,
                "error": str(e)
            }
    
    def _get_confidence_level(self, confidence: float) -> str:
        """
        Get categorical confidence level from numerical value.
        
        Args:
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            Confidence level category
        """
        if confidence >= 0.85:
            return "HIGH"
        elif confidence >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_uncertain_topics(self, uncertain_segments: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key topics from uncertain segments for verification.
        
        Args:
            uncertain_segments: List of uncertain text segments
            
        Returns:
            List of topics that need verification
        """
        topics = set()
        
        for segment in uncertain_segments:
            text = segment["text"]
            
            # Extract nouns and named entities (simplified approach)
            # In a real implementation, use NLP to extract key entities
            words = text.split()
            for word in words:
                # Simple filtering for potential topics (proper nouns, etc.)
                if len(word) > 3 and word[0].isupper():
                    topics.add(word.strip(".,;:!?'\"()"))
        
        return list(topics)
    
    def get_format_instructions(self) -> str:
        """
        Get format instructions for LLM-based confidence assessment.
        
        Returns:
            Format instructions string
        """
        return """
        Include a confidence assessment in JSON format at the end of your response:
        
        ```json
        {
          "confidence": 0.95,
          "uncertain_aspects": ["specific topic I'm less certain about"],
          "verification_suggested": false
        }
        ```
        
        Use a confidence value between 0.0 (completely uncertain) and 1.0 (completely certain).
        If there are specific aspects you're uncertain about, list them in the uncertain_aspects array.
        Set verification_suggested to true if your answer would benefit from additional verification.
        """ 