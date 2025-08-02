"""
Length variator enhancer for dynamically adjusting response length.

This module provides an enhancer that adjusts the length of LLM responses
based on context, user preferences, and configuration settings.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple

class LengthVariator:
    """
    Length variator enhancer for dynamically adjusting response length.
    
    This class provides methods to expand, condense, or otherwise adjust the
    length of LLM responses based on user preferences, conversation context,
    and bot-specific configuration.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm: Any = None,
        default_mode: str = "balanced",
        min_words_per_sentence: int = 5,
        max_expansion_factor: float = 1.5,
        max_reduction_factor: float = 0.5
    ):
        """
        Initialize length variator.
        
        Args:
            config_integration: Integration with the config system
            llm: Language model for complex transformations
            default_mode: Default length variation mode (concise, balanced, detailed)
            min_words_per_sentence: Minimum words per sentence (for splitting)
            max_expansion_factor: Maximum factor for expanding responses
            max_reduction_factor: Maximum factor for reducing responses
        """
        self.config_integration = config_integration
        self.llm = llm
        self.default_mode = default_mode
        self.min_words_per_sentence = min_words_per_sentence
        self.max_expansion_factor = max_expansion_factor
        self.max_reduction_factor = max_reduction_factor
        self.logger = logging.getLogger(__name__)
    
    def enhance(
        self, 
        response: str,
        bot_type: Optional[str] = None,
        mode: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Adjust the length of a response.
        
        Args:
            response: Original response to adjust
            bot_type: Type of bot (for configuration lookup)
            mode: Length variation mode (concise, balanced, detailed)
            context: Additional context for length adjustment
            
        Returns:
            Length-adjusted response
        """
        # Use provided mode or default
        variation_mode = mode or self.default_mode
        
        # Get bot-specific configuration if available
        if bot_type and self.config_integration:
            try:
                bot_config = self.config_integration.get_config(bot_type)
                enhancer_config = bot_config.get("enhancers", {}).get("length_variator", {})
                
                if "default_mode" in enhancer_config and not mode:
                    variation_mode = enhancer_config["default_mode"]
                    
                # Update other parameters if specified
                if "max_expansion_factor" in enhancer_config:
                    self.max_expansion_factor = enhancer_config["max_expansion_factor"]
                    
                if "max_reduction_factor" in enhancer_config:
                    self.max_reduction_factor = enhancer_config["max_reduction_factor"]
                    
            except Exception as e:
                self.logger.warning(f"Failed to load length variator config: {e}")
        
        # Context-based adjustments
        if context:
            # Adjust mode based on conversation context
            if "verbosity_preference" in context:
                variation_mode = context["verbosity_preference"]
            
            # Adjust mode based on query complexity
            if "query_complexity" in context:
                complexity = context["query_complexity"]
                if complexity == "high" and variation_mode == "concise":
                    # Complex questions need more detailed answers
                    variation_mode = "balanced"
                elif complexity == "low" and variation_mode == "detailed":
                    # Simple questions can be answered concisely
                    variation_mode = "balanced"
        
        # Apply length variation based on mode
        if variation_mode == "concise":
            return self._make_concise(response)
        elif variation_mode == "detailed":
            return self._make_detailed(response)
        else:  # balanced is default
            return response
    
    def _make_concise(self, text: str) -> str:
        """
        Make a response more concise.
        
        Args:
            text: Original text to condense
            
        Returns:
            Condensed text
        """
        # Use LLM-based approach if available
        if self.llm:
            try:
                return self._llm_based_condensing(text)
            except Exception as e:
                self.logger.warning(f"LLM-based condensing failed: {e}")
                # Fall back to rule-based approach
        
        # Rule-based approach for making text more concise
        condensed = text
        
        # Remove filler phrases
        filler_phrases = [
            r"\bI would like to mention that\b",
            r"\bIt's worth noting that\b",
            r"\bIt is important to understand that\b",
            r"\bI would like to point out that\b",
            r"\bAs you may already know,\b",
            r"\bFor your information,\b",
            r"\bIn my opinion,\b",
            r"\bTo put it simply,\b",
            r"\bIn other words,\b",
            r"\bBasically,\b",
            r"\bEssentially,\b",
            r"\bFundamentally,\b",
            r"\bIn essence,\b"
        ]
        
        for phrase in filler_phrases:
            condensed = re.sub(phrase, "", condensed, flags=re.IGNORECASE)
        
        # Remove redundant adverbs
        redundant_adverbs = [
            r"\bvery\b",
            r"\breally\b",
            r"\bquite\b",
            r"\bbasically\b",
            r"\bliterally\b",
            r"\bactually\b",
            r"\bcertainly\b",
            r"\bdefinitely\b",
            r"\bsimply\b",
            r"\bjust\b"
        ]
        
        for adverb in redundant_adverbs:
            condensed = re.sub(adverb, "", condensed, flags=re.IGNORECASE)
        
        # Collapse multiple spaces
        condensed = re.sub(r'\s+', ' ', condensed)
        
        # Ensure proper spacing after punctuation
        condensed = re.sub(r'([.!?])\s*', r'\1 ', condensed)
        
        # Clean up potential double spaces
        condensed = re.sub(r'\s+', ' ', condensed).strip()
        
        # If reduction is too extreme, moderate it
        if len(condensed) < len(text) * self.max_reduction_factor:
            # Too much was removed, so let's restore some of the original text
            return text
        
        return condensed
    
    def _make_detailed(self, text: str) -> str:
        """
        Make a response more detailed.
        
        Args:
            text: Original text to expand
            
        Returns:
            More detailed text
        """
        # Use LLM-based approach if available
        if self.llm:
            try:
                return self._llm_based_expansion(text)
            except Exception as e:
                self.logger.warning(f"LLM-based expansion failed: {e}")
                # Fall back to rule-based approach
        
        # Rule-based approach for adding more detail
        # Split into sentences for targeted expansion
        sentences = re.split(r'(?<=[.!?])\s+', text)
        expanded_sentences = []
        
        for sentence in sentences:
            # Skip empty or very short sentences
            if not sentence or len(sentence.split()) < self.min_words_per_sentence:
                expanded_sentences.append(sentence)
                continue
            
            # Expand sentences that mention key entities or concepts
            has_key_concept = re.search(r'\b(features?|benefits?|advantages?|disadvantages?|components?|options?|processes?|steps?|methods?)\b', sentence, re.IGNORECASE)
            
            if has_key_concept:
                # Add clarification or examples
                expanded = self._add_clarification(sentence)
                expanded_sentences.append(expanded)
            else:
                expanded_sentences.append(sentence)
        
        expanded_text = " ".join(expanded_sentences)
        
        # If expansion is too extreme, moderate it
        if len(expanded_text) > len(text) * self.max_expansion_factor:
            # Too much was added, so let's restore the original text
            return text
        
        return expanded_text
    
    def _add_clarification(self, sentence: str) -> str:
        """
        Add clarification or examples to a sentence.
        
        Args:
            sentence: Original sentence
            
        Returns:
            Expanded sentence with clarification
        """
        # Sample clarifying phrases
        clarifying_phrases = [
            ", which means {TOPIC}",
            ". This is important because {TOPIC}",
            ". For example, {TOPIC}",
            ", specifically {TOPIC}",
            " - a key point to understand",
            ", including various aspects"
        ]
        
        # Extract potential topics from sentence
        nouns = re.findall(r'\b([A-Z][a-z]+|[a-z]+(?:ing|ment|tion|sion|ence|ance|ity|ness|ship|hood))\b', sentence)
        
        if nouns:
            # Choose a random noun as the topic
            topic = nouns[-1]  # Often the last noun is the main subject
            
            # Choose a random clarifying phrase
            phrase = clarifying_phrases[0]  # Default to first phrase
            
            # Only use phrases that require a topic if we have one
            suitable_phrases = [p for p in clarifying_phrases if not "{TOPIC}" in p or nouns]
            if suitable_phrases:
                phrase = suitable_phrases[0]
            
            # Replace {TOPIC} placeholder if present
            if "{TOPIC}" in phrase:
                phrase = phrase.replace("{TOPIC}", topic)
            
            # Add clarification to end of sentence without final punctuation
            if sentence.endswith(".") or sentence.endswith("!") or sentence.endswith("?"):
                expanded = sentence[:-1] + phrase + sentence[-1]
            else:
                expanded = sentence + phrase
                
            return expanded
        
        return sentence
    
    def _llm_based_condensing(self, text: str) -> str:
        """
        Use LLM to make text more concise.
        
        Args:
            text: Text to condense
            
        Returns:
            Condensed text
        """
        if not self.llm:
            return text
        
        prompt = f"""
        Condense the following text to make it more concise and direct.
        Remove filler words, redundant phrases, and unnecessary details while preserving all key information.
        Aim for about 70% of the original length.
        
        Original text:
        ```
        {text}
        ```
        
        Concise version:
        """
        
        try:
            result = self.llm.predict(prompt)
            return result.strip()
        except Exception as e:
            self.logger.error(f"LLM condensing failed: {e}")
            return text
    
    def _llm_based_expansion(self, text: str) -> str:
        """
        Use LLM to make text more detailed.
        
        Args:
            text: Text to expand
            
        Returns:
            Expanded text
        """
        if not self.llm:
            return text
        
        prompt = f"""
        Expand the following text to make it more detailed and informative.
        Add clarifications, examples, or additional context where appropriate.
        Preserve the original meaning and tone.
        
        Original text:
        ```
        {text}
        ```
        
        Expanded version:
        """
        
        try:
            result = self.llm.predict(prompt)
            return result.strip()
        except Exception as e:
            self.logger.error(f"LLM expansion failed: {e}")
            return text
    
    def get_supported_modes(self) -> List[str]:
        """
        Get list of supported length variation modes.
        
        Returns:
            List of mode names
        """
        return ["concise", "balanced", "detailed"]
    
    def analyze_user_preference(
        self,
        user_messages: List[Dict[str, str]],
        session_id: str
    ) -> str:
        """
        Analyze user messages to determine verbosity preference.
        
        Args:
            user_messages: List of user message dictionaries
            session_id: Session identifier
            
        Returns:
            Inferred verbosity preference (concise, balanced, detailed)
        """
        # Default to balanced
        preference = "balanced"
        
        # Combine message texts
        text = " ".join([m.get("content", "") for m in user_messages])
        
        # Look for explicit preferences
        explicit_concise = re.search(r'\b(be (brief|concise|short)|keep it (brief|short)|summarize|in a nutshell|briefly|quickly|tl;dr)\b', text, re.IGNORECASE)
        explicit_detailed = re.search(r'\b(detailed|thorough|comprehensive|elaborate|explain (fully|in detail)|give me (details|more information))\b', text, re.IGNORECASE)
        
        if explicit_concise:
            preference = "concise"
        elif explicit_detailed:
            preference = "detailed"
        else:
            # Infer from message length
            total_words = sum(len(m.get("content", "").split()) for m in user_messages)
            avg_words = total_words / max(1, len(user_messages))
            
            if avg_words < 10:
                # Short messages suggest preference for concise answers
                preference = "concise"
            elif avg_words > 30:
                # Long messages suggest preference for detailed answers
                preference = "detailed"
        
        return preference 