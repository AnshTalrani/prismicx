"""
Pause inserter for creating more human-like responses.

This module inserts natural pauses into responses to simulate human typing
patterns and conversational rhythm, helping to avoid AI detection.
"""

import logging
import random
import re
from typing import Dict, Any, List, Optional, Tuple

class PauseInserter:
    """
    Inserts natural pauses and timing variations into responses.
    
    This class makes responses appear more human-like by:
    1. Adding natural pauses between sentences and paragraphs
    2. Simulating human typing patterns
    3. Creating conversational rhythm
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the pause inserter.
        
        Args:
            config: Configuration settings (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Default settings
        self.default_settings = {
            "natural_pauses": True,
            "typing_simulation": True,
            "sentence_pause_probability": 0.7,
            "paragraph_pause_probability": 0.9,
            "min_sentence_pause_ms": 500,
            "max_sentence_pause_ms": 1200,
            "min_paragraph_pause_ms": 1500,
            "max_paragraph_pause_ms": 3000,
            "typing_speed_wpm": {
                "min": 40,
                "max": 80
            },
            "typing_speed_variation": 0.2,  # 20% variation
            "pause_markers": {
                "sentence": "<pause>",
                "paragraph": "<long_pause>",
                "typing": "<typing>"
            }
        }
        
        # Merge with provided config
        self.settings = {**self.default_settings, **self.config}
    
    def insert_pauses(self, text: str, bot_type: Optional[str] = None) -> str:
        """
        Insert natural pauses into text to simulate human typing and conversation.
        
        Args:
            text: Input text
            bot_type: Type of bot (optional, for bot-specific settings)
            
        Returns:
            Text with pause markers inserted
        """
        try:
            # Apply bot-specific settings if available
            settings = self._get_bot_settings(bot_type)
            
            # Skip if natural pauses are disabled
            if not settings["natural_pauses"]:
                return text
            
            # Insert paragraph pauses
            text = self._insert_paragraph_pauses(text, settings)
            
            # Insert sentence pauses
            text = self._insert_sentence_pauses(text, settings)
            
            # Add typing simulation if enabled
            if settings["typing_simulation"]:
                text = self._add_typing_simulation(text, settings)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error inserting pauses: {e}")
            return text  # Return original text on error
    
    def _get_bot_settings(self, bot_type: Optional[str]) -> Dict[str, Any]:
        """
        Get settings specific to a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Settings dictionary
        """
        # Use default settings if no bot type specified
        if not bot_type:
            return self.settings
        
        # Check for bot-specific settings in config
        bot_settings = self.config.get(f"{bot_type}_settings", {})
        
        # Merge with default settings
        return {**self.settings, **bot_settings}
    
    def _insert_paragraph_pauses(self, text: str, settings: Dict[str, Any]) -> str:
        """
        Insert pauses between paragraphs.
        
        Args:
            text: Input text
            settings: Pause settings
            
        Returns:
            Text with paragraph pauses
        """
        # Define paragraph boundaries (double newline)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Skip if only one paragraph
        if len(paragraphs) <= 1:
            return text
        
        # Insert pauses with probability
        probability = settings["paragraph_pause_probability"]
        pause_marker = settings["pause_markers"]["paragraph"]
        
        result = []
        for i, paragraph in enumerate(paragraphs):
            result.append(paragraph)
            
            # Add pause after paragraph (except last one)
            if i < len(paragraphs) - 1 and random.random() < probability:
                pause_duration = random.randint(
                    settings["min_paragraph_pause_ms"],
                    settings["max_paragraph_pause_ms"]
                )
                result.append(f"{pause_marker}:{pause_duration}")
        
        return "\n\n".join(result)
    
    def _insert_sentence_pauses(self, text: str, settings: Dict[str, Any]) -> str:
        """
        Insert pauses between sentences.
        
        Args:
            text: Input text
            settings: Pause settings
            
        Returns:
            Text with sentence pauses
        """
        # Define sentence boundaries
        sentences = re.split(r'([.!?]\s+)', text)
        
        # Group sentences with their punctuation
        grouped_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                grouped_sentences.append(sentences[i] + sentences[i + 1])
            else:
                grouped_sentences.append(sentences[i])
        
        if len(sentences) % 2 == 1:
            grouped_sentences.append(sentences[-1])
        
        # Skip if only one sentence
        if len(grouped_sentences) <= 1:
            return text
        
        # Insert pauses with probability
        probability = settings["sentence_pause_probability"]
        pause_marker = settings["pause_markers"]["sentence"]
        
        result = []
        for i, sentence in enumerate(grouped_sentences):
            result.append(sentence)
            
            # Add pause after sentence (except last one)
            if i < len(grouped_sentences) - 1 and random.random() < probability:
                # Don't add pauses at paragraph breaks
                next_char = grouped_sentences[i + 1][0] if grouped_sentences[i + 1] else ""
                if next_char != "\n":
                    pause_duration = random.randint(
                        settings["min_sentence_pause_ms"],
                        settings["max_sentence_pause_ms"]
                    )
                    result.append(f"{pause_marker}:{pause_duration}")
        
        return "".join(result)
    
    def _add_typing_simulation(self, text: str, settings: Dict[str, Any]) -> str:
        """
        Add typing simulation markers.
        
        Args:
            text: Input text
            settings: Typing settings
            
        Returns:
            Text with typing simulation markers
        """
        # Calculate typing speed in characters per millisecond
        min_wpm = settings["typing_speed_wpm"]["min"]
        max_wpm = settings["typing_speed_wpm"]["max"]
        
        # Choose a random WPM within range
        wpm = random.uniform(min_wpm, max_wpm)
        
        # Convert WPM to characters per millisecond
        # Average word is ~5 characters, 1 minute = 60000 ms
        cpm = wpm * 5  # characters per minute
        cps = cpm / 60  # characters per second
        cpms = cps / 1000  # characters per millisecond
        
        # Calculate base typing time
        char_count = len(text)
        base_typing_time = int(char_count / cpms)
        
        # Apply variation
        variation = settings["typing_speed_variation"]
        typing_time = int(base_typing_time * random.uniform(1 - variation, 1 + variation))
        
        # Inject typing marker at the beginning
        typing_marker = settings["pause_markers"]["typing"]
        return f"{typing_marker}:{typing_time}{text}"
    
    def remove_pause_markers(self, text: str) -> str:
        """
        Remove pause markers from text.
        
        Args:
            text: Text with pause markers
            
        Returns:
            Clean text without markers
        """
        try:
            # Get all pause markers
            markers = self.settings["pause_markers"].values()
            
            # Create regex pattern for all markers
            pattern = "|".join([re.escape(marker) + r":\d+" for marker in markers])
            
            # Remove markers
            return re.sub(pattern, "", text)
            
        except Exception as e:
            self.logger.error(f"Error removing pause markers: {e}")
            return text  # Return original text on error
    
    def simulate_typing(
        self, 
        text: str, 
        bot_type: Optional[str] = None,
        callback: Optional[callable] = None
    ) -> None:
        """
        Simulate real-time typing of text with pauses.
        
        This method is designed to be used with chat interfaces that support
        incremental message delivery.
        
        Args:
            text: Text to simulate typing for
            bot_type: Type of bot (optional)
            callback: Function to call with incremental text
        """
        if callback is None:
            return
        
        try:
            # Insert pauses
            text_with_pauses = self.insert_pauses(text, bot_type)
            
            # Regex to find pause markers
            pause_pattern = re.compile(r'<(\w+)_pause>:(\d+)')
            typing_pattern = re.compile(r'<typing>:(\d+)')
            
            # Extract typing time if present
            typing_match = typing_pattern.search(text_with_pauses)
            if typing_match:
                # Remove typing marker
                text_with_pauses = typing_pattern.sub("", text_with_pauses)
            
            # Split on pause markers
            segments = []
            last_end = 0
            
            for match in pause_pattern.finditer(text_with_pauses):
                # Add text segment before pause
                segment_text = text_with_pauses[last_end:match.start()]
                if segment_text:
                    segments.append({"type": "text", "content": segment_text})
                
                # Add pause
                pause_type = match.group(1)
                pause_duration = int(match.group(2))
                segments.append({"type": "pause", "duration": pause_duration})
                
                last_end = match.end()
            
            # Add final segment
            final_segment = text_with_pauses[last_end:]
            if final_segment:
                segments.append({"type": "text", "content": final_segment})
            
            # Process segments
            accumulated_text = ""
            for segment in segments:
                if segment["type"] == "text":
                    accumulated_text += segment["content"]
                    callback(accumulated_text)
                elif segment["type"] == "pause":
                    import time
                    time.sleep(segment["duration"] / 1000)  # Convert ms to seconds
            
        except Exception as e:
            self.logger.error(f"Error simulating typing: {e}")
            # Fallback to sending complete text
            callback(self.remove_pause_markers(text))


# Create singleton instance
pause_inserter = PauseInserter() 