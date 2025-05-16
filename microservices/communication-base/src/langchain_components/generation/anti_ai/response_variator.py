"""
Response variator that applies multiple techniques to avoid AI detection.

This module provides a central response variator that coordinates multiple 
variability techniques to make AI-generated responses appear more human-like
while preserving semantic meaning.
"""

import logging
import random
from typing import Dict, Any, List, Optional, Union

class ResponseVariator:
    """
    Response variator that applies multiple techniques to avoid AI detection.
    
    This class coordinates multiple variability techniques to make AI-generated
    responses appear more human-like while preserving semantic meaning.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm: Any = None,
        level: str = "medium",
        techniques: Optional[List[str]] = None
    ):
        """
        Initialize response variator.
        
        Args:
            config_integration: Integration with the config system
            llm: Language model for complex variations
            level: Variability level ("low", "medium", "high")
            techniques: List of techniques to use (None for all)
        """
        self.config_integration = config_integration
        self.llm = llm
        self.level = level
        self.techniques = techniques or [
            "sentence_structure", 
            "punctuation", 
            "contractions", 
            "fillers",
            "informality",
            "vocabulary"
        ]
        self.logger = logging.getLogger(__name__)
        
        # Variability parameters based on level
        self.variability_params = self._get_variability_params(level)
        
        # Initialize technique-specific components
        self.technique_components = {}
    
    def _get_variability_params(self, level: str) -> Dict[str, float]:
        """
        Get variability parameters based on level.
        
        Args:
            level: Variability level ("low", "medium", "high")
            
        Returns:
            Dictionary of variability parameters
        """
        if level == "low":
            return {
                "sentence_structure_freq": 0.1,
                "punctuation_freq": 0.1,
                "contraction_freq": 0.3,
                "filler_freq": 0.1,
                "informality_level": 0.1,
                "vocabulary_variation": 0.1
            }
        elif level == "medium":
            return {
                "sentence_structure_freq": 0.3,
                "punctuation_freq": 0.3,
                "contraction_freq": 0.5,
                "filler_freq": 0.2,
                "informality_level": 0.3,
                "vocabulary_variation": 0.3
            }
        elif level == "high":
            return {
                "sentence_structure_freq": 0.5,
                "punctuation_freq": 0.5,
                "contraction_freq": 0.7,
                "filler_freq": 0.3,
                "informality_level": 0.5,
                "vocabulary_variation": 0.5
            }
        else:
            self.logger.warning(f"Unknown variability level: {level}, defaulting to medium")
            return self._get_variability_params("medium")
    
    def enhance(self, response: str, bot_type: Optional[str] = None) -> str:
        """
        Enhance response with variability techniques.
        
        Args:
            response: Original response
            bot_type: Type of bot (for config lookup)
            
        Returns:
            Enhanced response
        """
        # Skip empty responses
        if not response.strip():
            return response
        
        # Update parameters from config if available
        if bot_type and self.config_integration:
            config = self.config_integration.get_config(bot_type)
            self._update_params_from_config(config)
        
        # Apply techniques
        enhanced = response
        
        # Apply each technique based on configuration
        if "sentence_structure" in self.techniques:
            enhanced = self._vary_sentence_structure(enhanced)
        
        if "punctuation" in self.techniques:
            enhanced = self._vary_punctuation(enhanced)
        
        if "contractions" in self.techniques:
            enhanced = self._apply_contractions(enhanced)
        
        if "fillers" in self.techniques:
            enhanced = self._add_fillers(enhanced)
        
        if "informality" in self.techniques:
            enhanced = self._add_informality(enhanced)
        
        if "vocabulary" in self.techniques:
            enhanced = self._vary_vocabulary(enhanced)
        
        return enhanced
    
    def _update_params_from_config(self, config: Dict[str, Any]) -> None:
        """
        Update variability parameters from config.
        
        Args:
            config: Bot configuration
        """
        # Get anti-AI settings from config
        anti_ai = config.get("response_enhancement", {}).get("anti_ai", {})
        
        # Update level if specified
        if "variability_level" in anti_ai:
            level = anti_ai["variability_level"]
            self.level = level
            self.variability_params = self._get_variability_params(level)
        
        # Update specific parameters if provided
        technique_params = anti_ai.get("technique_params", {})
        for param, value in technique_params.items():
            if param in self.variability_params:
                self.variability_params[param] = value
        
        # Update techniques if specified
        if "techniques" in anti_ai:
            self.techniques = anti_ai["techniques"]
    
    def _vary_sentence_structure(self, text: str) -> str:
        """
        Vary sentence structure while preserving meaning.
        
        Args:
            text: Original text
            
        Returns:
            Text with varied sentence structure
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        varied_sentences = []
        
        for sentence in sentences:
            # Apply sentence structure variation based on frequency
            if random.random() < self.variability_params["sentence_structure_freq"]:
                varied = self._vary_single_sentence(sentence)
                varied_sentences.append(varied)
            else:
                varied_sentences.append(sentence)
        
        return " ".join(varied_sentences)
    
    def _vary_single_sentence(self, sentence: str) -> str:
        """
        Vary the structure of a single sentence.
        
        Args:
            sentence: Original sentence
            
        Returns:
            Varied sentence
        """
        # Apply simple rule-based transformations
        sentence = sentence.strip()
        
        # Skip short sentences
        if len(sentence.split()) < 4:
            return sentence
        
        # Apply transformations based on patterns
        if sentence.startswith("It is ") or sentence.startswith("There is "):
            # Invert structure: "It is important to note..." -> "Note that it's important..."
            parts = sentence.split(" ", 3)
            if len(parts) >= 4:
                match = parts[2]
                rest = parts[3]
                
                if match.endswith("ing"):
                    # "It is worth noting that..." -> "Notably, ..."
                    if "that" in rest:
                        clause = rest.split("that", 1)[1].strip()
                        return f"Notably, {clause}."
                
                if match == "important" and "to" in rest:
                    # "It is important to note..." -> "Note that..."
                    action = rest.split(" ", 2)
                    if len(action) >= 3 and action[0] == "to":
                        verb = action[1].strip()
                        content = action[2].strip()
                        return f"{verb.capitalize()} that {content}"
        
        elif sentence.startswith("You can ") or sentence.startswith("You should "):
            # Convert to suggestion: "You can try..." -> "Try..."
            parts = sentence.split(" ", 2)
            if len(parts) >= 3:
                verb = parts[2].strip()
                if " " in verb:
                    verb = verb.split(" ", 1)[0]
                rest = sentence.split(verb, 1)[1].strip()
                return f"{verb.capitalize()}{rest}"
        
        # If no specific rule applied, use more general approach
        words = sentence.split()
        if len(words) > 6 and random.random() < 0.5:
            # Move a phrase to the beginning or end
            mid_point = len(words) // 2
            
            if "," in sentence:
                # Use commas as natural break points
                parts = sentence.split(",")
                if len(parts) >= 2:
                    # Randomly reorganize parts around commas
                    random.shuffle(parts)
                    return ", ".join(parts)
            
            # Create a phrase from the second half and move it to the beginning
            first_half = " ".join(words[:mid_point])
            second_half = " ".join(words[mid_point:])
            
            if random.random() < 0.5 and not sentence.startswith("I ") and not sentence.startswith("You "):
                # Move second half to front: "The cat sat on the mat" -> "On the mat, the cat sat"
                return f"{second_half}, {first_half[0].lower() + first_half[1:]}"
        
        return sentence
    
    def _vary_punctuation(self, text: str) -> str:
        """
        Vary punctuation to appear more human-like.
        
        Args:
            text: Original text
            
        Returns:
            Text with varied punctuation
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        varied_sentences = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            
            # Skip empty or very short sentences
            if not sentence or len(sentence) < 5:
                if sentence:
                    varied_sentences.append(sentence)
                continue
            
            # Apply punctuation variation based on frequency
            if random.random() < self.variability_params["punctuation_freq"]:
                # Replace period with exclamation or question mark occasionally
                if sentence.endswith("."):
                    if "!" in sentence or "?" in sentence:
                        # Don't change if already has ! or ?
                        varied_sentences.append(sentence)
                    elif any(w in sentence.lower() for w in ["amazing", "great", "excellent", "fantastic"]):
                        # Add excitement for positive sentences
                        varied_sentences.append(sentence[:-1] + "!")
                    elif any(w in sentence.lower() for w in ["right", "correct", "sure", "agree"]) and len(sentence) < 30:
                        # Convert affirmations to questions sometimes
                        varied_sentences.append(sentence[:-1] + ", right?")
                    else:
                        varied_sentences.append(sentence)
                else:
                    varied_sentences.append(sentence)
            else:
                varied_sentences.append(sentence)
            
            # Occasionally add a trailing ellipsis between sentences
            if i < len(sentences) - 1 and random.random() < 0.1 and not sentence.endswith(("...", "!", "?")):
                varied_sentences[-1] = varied_sentences[-1][:-1] + "..."
        
        return " ".join(varied_sentences)
    
    def _apply_contractions(self, text: str) -> str:
        """
        Apply contractions to make text more natural.
        
        Args:
            text: Original text
            
        Returns:
            Text with contractions
        """
        # Common contractions mapping
        contractions = {
            "are not": "aren't",
            "cannot": "can't",
            "could not": "couldn't",
            "did not": "didn't",
            "does not": "doesn't",
            "do not": "don't",
            "had not": "hadn't",
            "has not": "hasn't",
            "have not": "haven't",
            "he is": "he's",
            "he would": "he'd",
            "I am": "I'm",
            "I have": "I've",
            "I will": "I'll",
            "I would": "I'd",
            "is not": "isn't",
            "it is": "it's",
            "it would": "it'd",
            "she is": "she's",
            "she would": "she'd",
            "that is": "that's",
            "there is": "there's",
            "they are": "they're",
            "they have": "they've",
            "they would": "they'd",
            "we are": "we're",
            "we have": "we've",
            "we would": "we'd",
            "were not": "weren't",
            "what is": "what's",
            "will not": "won't",
            "would not": "wouldn't",
            "you are": "you're",
            "you have": "you've",
            "you would": "you'd"
        }
        
        result = text
        
        # Apply each contraction with probability based on frequency
        for full, contracted in contractions.items():
            # Skip if the full form isn't in the text
            if full not in result:
                continue
            
            # Apply contraction with probability
            if random.random() < self.variability_params["contraction_freq"]:
                # Replace but be careful with word boundaries
                parts = result.split(full)
                result = ""
                for i, part in enumerate(parts):
                    result += part
                    if i < len(parts) - 1:
                        # Check if it's a word boundary
                        next_char = ""
                        if i < len(parts) - 1 and parts[i+1]:
                            next_char = parts[i+1][0]
                        
                        if not next_char or next_char.isspace() or next_char in ".,;:!?":
                            result += contracted
                        else:
                            result += full
        
        return result
    
    def _add_fillers(self, text: str) -> str:
        """
        Add filler words and phrases to sound more human.
        
        Args:
            text: Original text
            
        Returns:
            Text with filler words
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        varied_sentences = []
        
        # Filler phrases to potentially add
        beginning_fillers = [
            "Well, ", 
            "So, ", 
            "Basically, ", 
            "Actually, ", 
            "You know, ", 
            "I think ", 
            "In my view, "
        ]
        
        middle_fillers = [
            ", you know,", 
            ", like,", 
            ", I mean,", 
            ", basically,", 
            ", actually,"
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip empty or very short sentences
            if not sentence or len(sentence) < 10:
                if sentence:
                    varied_sentences.append(sentence)
                continue
            
            # Add beginning filler with low probability
            if random.random() < self.variability_params["filler_freq"] * 0.7:
                filler = random.choice(beginning_fillers)
                sentence = filler + sentence[0].lower() + sentence[1:]
            
            # Add middle filler with low probability for longer sentences
            words = sentence.split()
            if len(words) > 10 and random.random() < self.variability_params["filler_freq"] * 0.5:
                insert_pos = random.randint(3, len(words) - 3)
                filler = random.choice(middle_fillers)
                
                # Insert at word boundary
                before = " ".join(words[:insert_pos])
                after = " ".join(words[insert_pos:])
                sentence = before + filler + " " + after
            
            varied_sentences.append(sentence)
        
        return " ".join(varied_sentences)
    
    def _add_informality(self, text: str) -> str:
        """
        Add informal elements to make text more conversational.
        
        Args:
            text: Original text
            
        Returns:
            More informal text
        """
        # Skip if informality level is very low
        if self.variability_params["informality_level"] < 0.1:
            return text
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        varied_sentences = []
        
        # Informal elements
        interjections = ["oh", "ah", "wow", "hmm", "huh", "hey"]
        informal_endings = ["!", "..."]
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            
            # Skip empty or very short sentences
            if not sentence or len(sentence) < 5:
                if sentence:
                    varied_sentences.append(sentence)
                continue
            
            # Add interjection at the beginning for some sentences
            if i > 0 and random.random() < self.variability_params["informality_level"] * 0.3:
                interjection = random.choice(interjections)
                sentence = f"{interjection.capitalize()}, {sentence[0].lower() + sentence[1:]}"
            
            # Change ending punctuation for some sentences
            if sentence.endswith(".") and random.random() < self.variability_params["informality_level"] * 0.4:
                ending = random.choice(informal_endings)
                sentence = sentence[:-1] + ending
            
            varied_sentences.append(sentence)
        
        return " ".join(varied_sentences)
    
    def _vary_vocabulary(self, text: str) -> str:
        """
        Vary vocabulary to seem more human while preserving meaning.
        
        Args:
            text: Original text
            
        Returns:
            Text with varied vocabulary
        """
        # Skip if vocabulary variation is very low
        if self.variability_params["vocabulary_variation"] < 0.1:
            return text
        
        # Simple word substitutions
        substitutions = {
            "utilize": "use",
            "therefore": "so",
            "however": "but",
            "additionally": "also",
            "approximately": "about",
            "sufficient": "enough",
            "obtain": "get",
            "purchase": "buy",
            "require": "need",
            "assist": "help",
            "commence": "begin",
            "terminate": "end",
            "numerous": "many",
            "initial": "first",
            "currently": "now",
            "subsequently": "later",
            "prior to": "before",
            "following": "after"
        }
        
        result = text
        
        # Apply each substitution with probability based on vocabulary variation
        for formal, informal in substitutions.items():
            # Skip if the formal word isn't in the text
            if formal not in result:
                continue
            
            # Apply substitution with probability
            if random.random() < self.variability_params["vocabulary_variation"]:
                # Replace but be careful with word boundaries
                parts = result.split(formal)
                result = ""
                for i, part in enumerate(parts):
                    result += part
                    if i < len(parts) - 1:
                        # Check if it's a word boundary
                        prev_char = ""
                        if part:
                            prev_char = part[-1]
                        
                        next_char = ""
                        if i < len(parts) - 1 and parts[i+1]:
                            next_char = parts[i+1][0]
                        
                        is_boundary = (not prev_char or prev_char.isspace() or prev_char in ".,;:!?") and \
                                    (not next_char or next_char.isspace() or next_char in ".,;:!?")
                        
                        if is_boundary:
                            result += informal
                        else:
                            result += formal
        
        return result
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Basic sentence splitting
        for end_marker in [".", "!", "?"]:
            text = text.replace(f"{end_marker}\"", f"{end_marker}\" ")
        
        # Split on common sentence terminators but handle special cases
        split_markers = [".", "!", "?"]
        current_sentence = ""
        sentences = []
        
        for char in text:
            current_sentence += char
            
            if char in split_markers and len(current_sentence) > 1:
                # Check if this is an actual end of sentence
                sentence_ends = True
                
                # Check for common abbreviations
                for abbr in ["Mr.", "Mrs.", "Dr.", "St.", "vs.", "etc.", "i.e.", "e.g."]:
                    if current_sentence.strip().endswith(abbr):
                        sentence_ends = False
                        break
                
                if sentence_ends:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
        
        # Add any remaining text
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences 