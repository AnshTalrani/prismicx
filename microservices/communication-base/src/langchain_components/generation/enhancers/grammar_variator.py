"""
Grammar variator enhancer for varying grammar patterns in responses.

This module provides an enhancer that applies variations to grammar patterns
in LLM responses to create more human-like and diverse text structures.
"""

import logging
import re
import random
from typing import Dict, Any, List, Optional, Union, Set

class GrammarVariator:
    """
    Grammar variator enhancer for varying grammar patterns in responses.
    
    This class applies variations to grammar patterns in LLM responses to create
    more human-like and diverse text structures, helping to make AI-generated
    text less predictable and formulaic.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm: Any = None,
        variability_level: str = "medium",
        enabled_techniques: Optional[List[str]] = None
    ):
        """
        Initialize grammar variator.
        
        Args:
            config_integration: Integration with the config system
            llm: Language model for complex transformations
            variability_level: Level of grammar variability (low, medium, high)
            enabled_techniques: List of enabled variation techniques
        """
        self.config_integration = config_integration
        self.llm = llm
        self.variability_level = variability_level
        self.enabled_techniques = enabled_techniques or [
            "sentence_structure",
            "conjunctions",
            "tense_variation",
            "passive_to_active",
            "active_to_passive",
            "modifier_placement"
        ]
        self.logger = logging.getLogger(__name__)
        
        # Initialize variation patterns
        self._init_variation_patterns()
    
    def _init_variation_patterns(self) -> None:
        """
        Initialize patterns for grammar variations.
        """
        # Sentence structure variations
        self.compound_pattern = re.compile(r'\b(and|or|but|so)\b')
        self.clause_start_pattern = re.compile(r'(?<=[.!?])\s+([A-Z][^.!?;]{10,}?)(,|\.|!|\?|;)')
        
        # Conjunction variations (expand beyond just 'and', 'but', 'or')
        self.conjunction_replacements = {
            'and': ['also', 'plus', 'along with', 'as well as', 'additionally', 'furthermore', 'moreover'],
            'but': ['however', 'yet', 'still', 'nevertheless', 'on the other hand', 'conversely', 'though'],
            'so': ['therefore', 'thus', 'consequently', 'as a result', 'hence'],
            'because': ['since', 'as', 'given that', 'considering that', 'due to the fact that'],
            'if': ['provided that', 'assuming that', 'in the event that', 'on condition that']
        }
        
        # Phrase replacements for common constructions
        self.phrase_replacements = {
            r'\bI think\b': ['I believe', 'In my opinion', 'I feel that', 'I reckon', 'It seems to me'],
            r'\bit is important to\b': ['it matters to', 'it\'s crucial to', 'it\'s vital to', 'it\'s essential to'],
            r'\bin order to\b': ['to', 'so as to', 'as a means to', 'for the purpose of'],
            r'\bfor example\b': ['for instance', 'as an example', 'to illustrate', 'by way of example', 'case in point']
        }
        
        # Passive voice patterns
        self.passive_pattern = re.compile(r'\b(is|are|was|were|be|been|being)\s+(\w+ed|built|bought|sold|made|done|said|known|given|shown|told|sent|brought)\b')
        
        # Active voice transformations
        self.active_pattern = re.compile(r'\b([A-Z]\w+|\b(I|we|they|he|she|it))\s+(\w+s|have|has|had)\s+')
        
        # Modifier placement patterns
        self.modifier_pattern = re.compile(r',\s+(however|therefore|nevertheless|consequently|subsequently|moreover|furthermore|additionally)')
    
    def enhance(
        self, 
        response: str,
        bot_type: Optional[str] = None,
        level: Optional[str] = None,
        techniques: Optional[List[str]] = None
    ) -> str:
        """
        Apply grammar variations to a response.
        
        Args:
            response: Original response to enhance
            bot_type: Type of bot (for configuration lookup)
            level: Variability level to use (overrides instance setting)
            techniques: Specific techniques to use (overrides instance setting)
            
        Returns:
            Enhanced response with grammar variations
        """
        # Use provided level or default
        variability_level = level or self.variability_level
        
        # Get bot-specific configuration if available
        if bot_type and self.config_integration:
            try:
                bot_config = self.config_integration.get_config(bot_type)
                enhancer_config = bot_config.get("enhancers", {}).get("grammar_variator", {})
                
                if "level" in enhancer_config and not level:
                    variability_level = enhancer_config["level"]
                
                if "techniques" in enhancer_config and not techniques:
                    techniques = enhancer_config["techniques"]
            except Exception as e:
                self.logger.warning(f"Failed to load grammar variator config: {e}")
        
        # Use provided techniques or instance default
        active_techniques = techniques or self.enabled_techniques
        
        # Get variation parameters based on level
        params = self._get_variability_params(variability_level)
        
        # Apply LLM-based approach if available and level is high
        if self.llm and variability_level == "high":
            try:
                return self._llm_grammar_variation(response)
            except Exception as e:
                self.logger.warning(f"LLM-based grammar variation failed: {e}")
                # Continue with rule-based approach as fallback
        
        # Apply rule-based grammar variations
        enhanced_response = response
        
        # Split into sentences for more controlled processing
        sentences = re.split(r'(?<=[.!?])\s+', enhanced_response)
        processed_sentences = []
        
        for sentence in sentences:
            # Skip empty or very short sentences
            if not sentence or len(sentence) < 10:
                processed_sentences.append(sentence)
                continue
                
            processed = sentence
            
            # Apply selected techniques to sentence based on random chance
            if "sentence_structure" in active_techniques and random.random() < params["sentence_rewrite_chance"]:
                processed = self._vary_sentence_structure(processed)
                
            if "conjunctions" in active_techniques and random.random() < params["conjunction_replace_chance"]:
                processed = self._vary_conjunctions(processed)
                
            if "tense_variation" in active_techniques and random.random() < params["tense_change_chance"]:
                processed = self._vary_tense(processed)
                
            if "passive_to_active" in active_techniques and self.passive_pattern.search(processed) and random.random() < params["voice_change_chance"]:
                processed = self._passive_to_active(processed)
                
            if "active_to_passive" in active_techniques and self.active_pattern.search(processed) and random.random() < params["voice_change_chance"]:
                processed = self._active_to_passive(processed)
                
            if "modifier_placement" in active_techniques and self.modifier_pattern.search(processed) and random.random() < params["modifier_move_chance"]:
                processed = self._vary_modifier_placement(processed)
                
            # Apply phrase replacements with configured chance
            processed = self._apply_phrase_replacements(processed, params["phrase_replace_chance"])
            
            processed_sentences.append(processed)
        
        # Combine processed sentences
        enhanced_response = " ".join(processed_sentences)
        
        return enhanced_response
    
    def _get_variability_params(self, level: str) -> Dict[str, float]:
        """
        Get variability parameters based on the specified level.
        
        Args:
            level: Variability level (low, medium, high)
            
        Returns:
            Dictionary of variability parameters
        """
        if level == "low":
            return {
                "sentence_rewrite_chance": 0.1,
                "conjunction_replace_chance": 0.2,
                "tense_change_chance": 0.05,
                "voice_change_chance": 0.1,
                "modifier_move_chance": 0.1,
                "phrase_replace_chance": 0.2
            }
        elif level == "high":
            return {
                "sentence_rewrite_chance": 0.4,
                "conjunction_replace_chance": 0.6,
                "tense_change_chance": 0.2,
                "voice_change_chance": 0.3,
                "modifier_move_chance": 0.4,
                "phrase_replace_chance": 0.5
            }
        else:  # medium is default
            return {
                "sentence_rewrite_chance": 0.2,
                "conjunction_replace_chance": 0.4,
                "tense_change_chance": 0.1,
                "voice_change_chance": 0.2,
                "modifier_move_chance": 0.2,
                "phrase_replace_chance": 0.3
            }
    
    def _llm_grammar_variation(self, text: str) -> str:
        """
        Use LLM to apply grammar variations.
        
        Args:
            text: Text to apply variations to
            
        Returns:
            Text with grammar variations
        """
        if not self.llm:
            return text
        
        prompt = f"""
        Rewrite the following text with varied grammar patterns while preserving meaning.
        Apply these techniques:
        - Vary sentence structures (simple, compound, complex)
        - Mix active and passive voice
        - Vary tense usage where appropriate
        - Use different conjunctions and transitions
        - Vary modifier placement
        
        Original text:
        ```
        {text}
        ```
        
        Rewritten text with varied grammar:
        """
        
        try:
            result = self.llm.predict(prompt)
            return result.strip()
        except Exception as e:
            self.logger.error(f"LLM grammar variation failed: {e}")
            return text
    
    def _vary_sentence_structure(self, sentence: str) -> str:
        """
        Vary sentence structure.
        
        Args:
            sentence: Sentence to apply variation to
            
        Returns:
            Sentence with varied structure
        """
        # Convert simple sentence to compound with conjunction
        if len(sentence) > 30 and "," in sentence and random.random() < 0.5:
            # Find a comma-delimited clause to convert
            comma_parts = sentence.split(",", 1)
            if len(comma_parts) > 1:
                conjunctions = ["and", "but", "so", "while", "whereas", "although"]
                conjunction = random.choice(conjunctions)
                return comma_parts[0] + " " + conjunction + comma_parts[1]
        
        # Convert compound sentence to two simpler sentences
        compound_match = self.compound_pattern.search(sentence)
        if compound_match and random.random() < 0.3:
            # Split at the conjunction
            conjunction = compound_match.group(0)
            parts = sentence.split(conjunction, 1)
            if len(parts) == 2 and len(parts[0]) > 10 and len(parts[1]) > 10:
                # Make sure the second part can stand as a sentence
                second_part = parts[1].strip()
                if not second_part[0].isupper():
                    # Try to capitalize the first letter
                    second_part = second_part[0].upper() + second_part[1:]
                return f"{parts[0].strip()}. {second_part}"
        
        # Move dependent clause to beginning
        match = re.search(r'(.*?), (because|although|when|if|since|while) (.*)', sentence)
        if match and random.random() < 0.4:
            main_clause = match.group(1)
            subordinator = match.group(2)
            dependent_clause = match.group(3)
            
            # Capitalize subordinator
            subordinator = subordinator[0].upper() + subordinator[1:]
            
            # Ensure main clause can stand alone
            if dependent_clause.endswith("."):
                dependent_clause = dependent_clause[:-1]
                
            return f"{subordinator} {dependent_clause}, {main_clause}."
            
        return sentence
    
    def _vary_conjunctions(self, sentence: str) -> str:
        """
        Replace conjunctions with variations.
        
        Args:
            sentence: Sentence to apply variation to
            
        Returns:
            Sentence with varied conjunctions
        """
        for conjunction, alternatives in self.conjunction_replacements.items():
            pattern = re.compile(rf'\b{conjunction}\b')
            
            # Find all matches first
            matches = list(pattern.finditer(sentence))
            
            # Only replace one conjunction per sentence to avoid over-editing
            if matches:
                # Choose a random match to replace
                match = random.choice(matches)
                alternative = random.choice(alternatives)
                
                # Replace only this specific match
                start, end = match.span()
                sentence = sentence[:start] + alternative + sentence[end:]
                
                # Break after one replacement
                break
                
        return sentence
    
    def _vary_tense(self, sentence: str) -> str:
        """
        Apply tense variations.
        
        Args:
            sentence: Sentence to apply variation to
            
        Returns:
            Sentence with varied tense
        """
        # This is a simplified approach - a comprehensive tense variation
        # would require more sophisticated NLP analysis
        
        # Convert present continuous to simple present (is/are verb+ing -> verb+s)
        match = re.search(r'\b(is|are)\s+(\w+ing)\b', sentence)
        if match and random.random() < 0.4:
            continuous = match.group(0)
            verb_base = match.group(2)[:-3]  # Remove 'ing'
            
            # Simplistic conjugation - would need more rules for a complete solution
            if match.group(1) == "is":
                replacement = verb_base + "s"
            else:  # are
                replacement = verb_base
                
            sentence = sentence.replace(continuous, replacement, 1)
            
        # Convert present perfect to simple past (have/has verb+ed -> verb+ed)
        match = re.search(r'\b(have|has)\s+(\w+ed)\b', sentence)
        if match and random.random() < 0.4:
            perfect = match.group(0)
            past_form = match.group(2)
            sentence = sentence.replace(perfect, past_form, 1)
            
        return sentence
    
    def _passive_to_active(self, sentence: str) -> str:
        """
        Convert passive voice to active voice.
        
        Args:
            sentence: Sentence to apply variation to
            
        Returns:
            Sentence with passive converted to active
        """
        # This is a simplified approach that works for basic cases
        # A full implementation would require parsing and understanding subject-verb-object
        
        match = re.search(r'\b(is|are|was|were)\s+(\w+ed|built|bought|sold|made|done|said|known)\s+by\s+([^.!?,;]+)', sentence)
        if match:
            passive_construct = match.group(0)
            auxiliary = match.group(1)
            verb = match.group(2)
            actor = match.group(3).strip()
            
            # Extract the subject (what comes before the passive construction)
            parts = sentence.split(passive_construct, 1)
            if len(parts) == 2:
                prefix = parts[0].strip()
                suffix = parts[1].strip()
                
                # Find the subject (simplistic - assumes it's right before the passive)
                subject_match = re.search(r'(?:The|A|An|This|That|These|Those)?\s*([^\s]+(?:\s+[^\s]+)?)\s*$', prefix)
                if subject_match:
                    subject = subject_match.group(1)
                    subject_prefix = prefix[:subject_match.start()]
                    
                    # Attempt to create active voice
                    active = f"{subject_prefix}{actor} {verb} {subject} {suffix}"
                    return active
                    
        return sentence
    
    def _active_to_passive(self, sentence: str) -> str:
        """
        Convert active voice to passive voice.
        
        Args:
            sentence: Sentence to apply variation to
            
        Returns:
            Sentence with active converted to passive
        """
        # This is a simplified approach that works for basic cases
        # A full implementation would require parsing and understanding subject-verb-object
        
        # Look for <subject> <verb> <object> pattern
        match = re.search(r'([A-Z]\w+|\b(?:I|we|they|he|she|it))\s+(\w+s|have|has|had)\s+([^.,;!?]+)', sentence, re.IGNORECASE)
        if match:
            active_construct = match.group(0)
            subject = match.group(1)
            verb = match.group(2)
            object_phrase = match.group(3).strip()
            
            # Convert verb to passive form (simplistic)
            if verb.endswith('s'):
                passive_verb = "is " + verb[:-1] + "ed"
            elif verb == "have":
                passive_verb = "are"
            elif verb == "has":
                passive_verb = "is"
            elif verb == "had":
                passive_verb = "was"
            else:
                # Default fallback
                passive_verb = "is " + verb + "ed"
            
            # Create passive construction
            passive = f"{object_phrase} {passive_verb} by {subject}"
            
            # Replace in original sentence
            parts = sentence.split(active_construct, 1)
            if len(parts) == 2:
                return parts[0] + passive + parts[1]
                
        return sentence
    
    def _vary_modifier_placement(self, sentence: str) -> str:
        """
        Vary placement of modifiers in sentence.
        
        Args:
            sentence: Sentence to apply variation to
            
        Returns:
            Sentence with varied modifier placement
        """
        # Move modifiers from mid-sentence to beginning
        match = re.search(r',\s+(however|therefore|nevertheless|consequently|subsequently|moreover|furthermore|additionally)[,]\s+', sentence)
        if match:
            modifier = match.group(1)
            modified = sentence.replace(match.group(0), " ")
            modified = modifier.capitalize() + ", " + modified[0].lower() + modified[1:]
            return modified
            
        # Move front-loaded modifiers to mid-sentence
        match = re.search(r'^(However|Therefore|Nevertheless|Consequently|Subsequently|Moreover|Furthermore|Additionally),\s+', sentence)
        if match:
            modifier = match.group(1).lower()
            rest = sentence[match.end():]
            
            # Find a good spot for the modifier (after subject-verb if possible)
            sv_match = re.search(r'^([^,\.]{10,30})[,\.]?', rest)
            if sv_match:
                modified = sv_match.group(1) + ", " + modifier + "," + rest[sv_match.end():]
                return modified
                
        return sentence
    
    def _apply_phrase_replacements(self, sentence: str, replace_chance: float) -> str:
        """
        Apply phrase replacement variations.
        
        Args:
            sentence: Sentence to apply variation to
            replace_chance: Chance to replace each matched phrase
            
        Returns:
            Sentence with phrase replacements
        """
        for pattern, alternatives in self.phrase_replacements.items():
            # Only attempt replacement with the specified chance
            if random.random() > replace_chance:
                continue
                
            # Find all matches of this pattern
            matches = list(re.finditer(pattern, sentence, re.IGNORECASE))
            
            # Only replace one instance per pattern to avoid over-editing
            if matches:
                # Choose a random match to replace
                match = random.choice(matches)
                alternative = random.choice(alternatives)
                
                # Replace only this specific match
                start, end = match.span()
                sentence = sentence[:start] + alternative + sentence[end:]
                
        return sentence
    
    def get_supported_techniques(self) -> List[str]:
        """
        Get list of supported grammar variation techniques.
        
        Returns:
            List of technique names
        """
        return [
            "sentence_structure",
            "conjunctions",
            "tense_variation",
            "passive_to_active",
            "active_to_passive",
            "modifier_placement"
        ] 