"""
Text processor component for the analysis-base microservice.

This module provides the TextProcessor component for processing textual data
based on declarative specifications.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set, Union

from src.processing.components.contracts.base_contracts import TransformerContract
from src.processing.spec_interpreter import get_interpreter


class TextProcessor(TransformerContract):
    """
    Text processor component that transforms text based on specifications.
    
    This component processes text data according to the operations defined in
    a specification, such as tokenization, normalization, stopword removal, etc.
    
    Attributes:
        logger (logging.Logger): Logger for the text processor
        component_id (str): Unique identifier for the component
        name (str): Name of the component
        description (str): Description of the component
        config (Dict[str, Any]): Configuration for the component
        model_config (Dict[str, Any]): Model configuration from spec interpreter
        processors (List[Dict[str, Any]]): List of text processors to apply
    """
    
    def __init__(
        self,
        component_id: str,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize the text processor component.
        
        Args:
            component_id: Unique identifier for the component
            name: Name of the component
            description: Description of the component
            config: Configuration for the component
            model_name: Name of the model specification to load
        """
        super().__init__(component_id, name, description, config or {})
        
        self.logger = logging.getLogger(f"component.{self.__class__.__name__}.{component_id}")
        
        # Load the model specification if provided
        self.model_config = None
        if model_name:
            spec_interpreter = get_interpreter()
            try:
                model_spec = spec_interpreter.load_model_spec(model_name)
                self.model_config = spec_interpreter.interpret_model_spec(model_spec)
                self.logger.info(f"Loaded text processor model: {model_name}")
            except Exception as e:
                self.logger.error(f"Error loading text processor model {model_name}: {str(e)}")
                raise ValueError(f"Failed to load text processor model: {str(e)}")
        
        # Initialize processors based on model config or direct configuration
        self.processors = []
        if self.model_config and "processors" in self.model_config:
            self.processors = self.model_config["processors"]
        elif "processors" in self.config:
            self.processors = self.config["processors"]
        else:
            self.logger.warning("No processors defined for TextProcessor component")
            
        # Language setting
        self.language = self.model_config.get("language", "en") if self.model_config else self.config.get("language", "en")
        
        # Initialize stopwords if needed
        self._stopwords = self._load_stopwords()
            
        self.logger.info(f"Initialized TextProcessor with {len(self.processors)} processors")
    
    async def transform(self, data: Any, context: Dict[str, Any] = None) -> Any:
        """
        Transform text data by applying configured processors.
        
        Args:
            data: Text data to process (string or list of strings)
            context: Processing context
            
        Returns:
            Processed text data
            
        Raises:
            ValueError: If data is not a string or list of strings
        """
        context = context or {}
        
        # Handle different data types
        if isinstance(data, str):
            return self._process_text(data)
        elif isinstance(data, list):
            return [self._process_text(item) if isinstance(item, str) else item for item in data]
        elif isinstance(data, dict) and "text" in data:
            # Process text field in dictionary
            result = data.copy()
            result["text"] = self._process_text(data["text"])
            return result
        else:
            self.logger.error(f"Unsupported data type for TextProcessor: {type(data)}")
            raise ValueError(f"TextProcessor requires string, list of strings, or dict with 'text' field")
    
    def _process_text(self, text: str) -> str:
        """
        Process a single text string.
        
        Args:
            text: Text to process
            
        Returns:
            Processed text
        """
        processed_text = text
        
        # Apply each processor in sequence
        for processor in self.processors:
            processor_type = processor.get("type")
            processor_config = processor.get("config", {})
            
            try:
                if processor_type == "lowercase":
                    processed_text = self._apply_lowercase(processed_text)
                elif processor_type == "remove_punctuation":
                    processed_text = self._apply_remove_punctuation(processed_text, **processor_config)
                elif processor_type == "remove_stopwords":
                    processed_text = self._apply_remove_stopwords(processed_text, **processor_config)
                elif processor_type == "normalize_whitespace":
                    processed_text = self._apply_normalize_whitespace(processed_text)
                elif processor_type == "strip":
                    processed_text = self._apply_strip(processed_text)
                elif processor_type == "replace_pattern":
                    processed_text = self._apply_replace_pattern(processed_text, **processor_config)
                elif processor_type == "tokenize":
                    # Tokenization returns a list, but we're keeping the processor chain as string operations
                    # So we join tokens back into a string
                    tokens = self._apply_tokenize(processed_text, **processor_config)
                    processed_text = " ".join(tokens)
                else:
                    self.logger.warning(f"Unknown processor type: {processor_type}")
            except Exception as e:
                self.logger.error(f"Error applying processor {processor_type}: {str(e)}")
                # Continue with next processor
        
        return processed_text
    
    def _apply_lowercase(self, text: str) -> str:
        """
        Convert text to lowercase.
        
        Args:
            text: Text to convert
            
        Returns:
            Lowercase text
        """
        return text.lower()
    
    def _apply_remove_punctuation(self, text: str, keep_chars: str = "") -> str:
        """
        Remove punctuation from text.
        
        Args:
            text: Text to process
            keep_chars: Punctuation characters to preserve
            
        Returns:
            Text with punctuation removed
        """
        import string
        
        # Determine which punctuation to remove
        chars_to_remove = set(string.punctuation) - set(keep_chars)
        
        # Create a translation table
        table = str.maketrans("", "", "".join(chars_to_remove))
        
        # Apply the translation
        return text.translate(table)
    
    def _apply_remove_stopwords(self, text: str, min_length: int = 0) -> str:
        """
        Remove stopwords from text.
        
        Args:
            text: Text to process
            min_length: Minimum word length to keep
            
        Returns:
            Text with stopwords removed
        """
        # Tokenize the text
        words = text.split()
        
        # Filter out stopwords and short words
        filtered_words = [
            word for word in words 
            if word.lower() not in self._stopwords and len(word) >= min_length
        ]
        
        # Join the filtered words back into a string
        return " ".join(filtered_words)
    
    def _apply_normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text to process
            
        Returns:
            Text with normalized whitespace
        """
        # Replace all whitespace with a single space
        return re.sub(r'\s+', ' ', text)
    
    def _apply_strip(self, text: str) -> str:
        """
        Strip whitespace from the beginning and end of text.
        
        Args:
            text: Text to strip
            
        Returns:
            Stripped text
        """
        return text.strip()
    
    def _apply_replace_pattern(self, text: str, pattern: str, replacement: str = "", flags: int = 0) -> str:
        """
        Replace regex pattern in text.
        
        Args:
            text: Text to process
            pattern: Regex pattern to match
            replacement: Replacement string
            flags: Regex flags
            
        Returns:
            Text with pattern replaced
        """
        return re.sub(pattern, replacement, text, flags=flags)
    
    def _apply_tokenize(self, text: str, delimiter: str = r'\s+') -> List[str]:
        """
        Tokenize text.
        
        Args:
            text: Text to tokenize
            delimiter: Delimiter regex pattern
            
        Returns:
            List of tokens
        """
        # Split text by delimiter
        tokens = re.split(delimiter, text)
        
        # Remove empty tokens
        return [token for token in tokens if token]
    
    def _load_stopwords(self) -> Set[str]:
        """
        Load stopwords for the configured language.
        
        Returns:
            Set of stopwords
        """
        # English stopwords as a fallback
        default_stopwords = {
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
            "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
            "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
            "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
            "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
            "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
            "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
            "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "s", "t", "can", "will", "just", "don", "don't", "should",
            "should've", "now", "d", "ll", "m", "o", "re", "ve", "y", "ain", "aren", "aren't",
            "couldn", "couldn't", "didn", "didn't", "doesn", "doesn't", "hadn", "hadn't", "hasn",
            "hasn't", "haven", "haven't", "isn", "isn't", "ma", "mightn", "mightn't", "mustn",
            "mustn't", "needn", "needn't", "shan", "shan't", "shouldn", "shouldn't", "wasn",
            "wasn't", "weren", "weren't", "won", "won't", "wouldn", "wouldn't"
        }
        
        # Check if we should use additional or custom stopwords
        custom_stopwords = []
        
        # From model config
        if self.model_config and "stopwords" in self.model_config:
            custom_stopwords = self.model_config["stopwords"]
        # From component config
        elif "stopwords" in self.config:
            custom_stopwords = self.config["stopwords"]
        
        # If explicit stopwords are provided, use those instead of defaults
        if custom_stopwords:
            if isinstance(custom_stopwords, list):
                return set(custom_stopwords)
            elif isinstance(custom_stopwords, dict) and self.language in custom_stopwords:
                return set(custom_stopwords[self.language])
        
        # Otherwise return default stopwords
        return default_stopwords 