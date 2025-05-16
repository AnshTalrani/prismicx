"""
Semantic understanding component for natural language processing.
Provides capabilities for understanding the deeper contextual meaning of text.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from src.langchain_components.llm.llm_factory import llm_factory


class SemanticUnderstandingResult(BaseModel):
    """Schema for semantic understanding results."""
    main_topics: List[str] = Field(description="Main topics identified in the text")
    sentiment: str = Field(
        description="Overall sentiment of the text (positive, negative, neutral)"
    )
    emotional_tone: str = Field(description="Emotional tone of the text")
    context_references: List[Dict[str, Any]] = Field(
        description="References to contextual information such as times, places, events",
        default_factory=list
    )
    key_concepts: List[str] = Field(description="Key concepts identified in the text")
    user_needs: Optional[List[str]] = Field(
        description="Identified user needs or problems",
        default=None
    )


class SemanticUnderstanding:
    """
    Analyzes text for deeper contextual meaning.

    Provides capabilities for understanding the semantic content of messages,
    including topics, sentiment, emotional tone, and key concepts.
    """

    def __init__(self):
        """Initialize the semantic understanding component."""
        self.logger = logging.getLogger(__name__)

        # Define default prompt template
        self.default_prompt = ChatPromptTemplate.from_template(
            """Analyze the following text for deeper semantic understanding.
            Return a JSON object with these fields:
            - main_topics: list of main topics identified
            - sentiment: overall sentiment (positive, negative, neutral)
            - emotional_tone: emotional tone of the text
            - context_references: list of contextual references (times, places, events)
            - key_concepts: list of key concepts identified
            - user_needs: list of identified user needs or problems

            Text to analyze: {input}

            JSON Response:"""
        )

        # Setup default parser
        self.default_parser = JsonOutputParser(pydantic_object=SemanticUnderstandingResult)

    def analyze(
        self,
        text: str,
        bot_type: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        custom_prompt: Optional[ChatPromptTemplate] = None,
        custom_parser: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze text for semantic understanding.

        Args:
            text: The text to analyze
            bot_type: Type of bot to get configuration for
            model_name: Specific model to use for analysis
            temperature: Temperature setting for the model
            custom_prompt: Custom prompt to use instead of default
            custom_parser: Custom parser to use instead of default

        Returns:
            Dictionary containing semantic analysis results
        """
        try:
            # Get model
            llm = llm_factory.get_llm(
                model_name=model_name,
                temperature=temperature or 0.2,  # Lower temperature for more consistent analysis
                bot_type=bot_type
            )

            # Use provided prompt or default
            prompt = custom_prompt or self.default_prompt

            # Use provided parser or default
            parser = custom_parser or self.default_parser

            # Create chain
            chain = prompt | llm | parser

            # Run chain
            result = chain.invoke({"input": text})

            # Return dictionary (either from pydantic model or direct JSON)
            if hasattr(result, "dict"):
                return result.dict()
            return result

        except Exception as e:
            self.logger.error("Error in semantic analysis: %s", str(e))
            # Return minimal result on error
            return {
                "main_topics": [],
                "sentiment": "unknown",
                "emotional_tone": "unknown",
                "context_references": [],
                "key_concepts": [],
                "user_needs": []
            }

    def extract_custom_semantic_features(
        self,
        text: str,
        feature_definitions: List[Dict[str, str]],
        bot_type: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract custom semantic features from text.

        Args:
            text: The text to analyze
            feature_definitions: List of feature definitions with 'name' and 'description'
            bot_type: Type of bot to get configuration for
            model_name: Specific model to use for analysis

        Returns:
            Dictionary with extracted features
        """
        try:
            # Validate feature definitions
            if not feature_definitions or not isinstance(feature_definitions, list):
                raise ValueError("Feature definitions must be a non-empty list")

            # Format feature descriptions for prompt
            features_prompt = "\n".join([
                f"- {f['name']}: {f['description']}"
                for f in feature_definitions
            ])

            # Create custom prompt
            prompt = ChatPromptTemplate.from_template(
                """Analyze the following text and extract these specific semantic features:
                {features}

                Return your analysis as a JSON object where keys are the feature names and
                values are the extracted information.

                Text to analyze: {input}

                JSON Response:"""
            )

            # Get model
            llm = llm_factory.get_llm(
                model_name=model_name,
                temperature=0.1,  # Use very low temperature for consistency
                bot_type=bot_type
            )

            # Create simple chain with string output parser
            chain = prompt | llm | StrOutputParser()

            # Run chain
            result_str = chain.invoke({
                "input": text,
                "features": features_prompt
            })

            # Parse JSON from string
            try:
                result = json.loads(result_str)
                return result
            except json.JSONDecodeError:
                self.logger.error("Failed to parse JSON from model output")
                # Simple extraction fallback if JSON parsing fails
                return self._extract_json_fallback(
                    result_str,
                    [f['name'] for f in feature_definitions]
                )

        except Exception as e:
            self.logger.error("Error in custom semantic feature extraction: %s", str(e))
            # Return empty result
            return {f['name']: None for f in feature_definitions}

    def _extract_json_fallback(self, text: str, feature_names: List[str]) -> Dict[str, Any]:
        """
        Fallback method to extract JSON-like content from text.

        Args:
            text: Text that should contain JSON
            feature_names: List of expected feature names

        Returns:
            Dictionary with extracted features
        """
        result = {name: None for name in feature_names}

        # Look for patterns like "name": "value" or "name": [items]
        for name in feature_names:
            # Try to find the feature in the text
            pattern = r'"' + re.escape(name) + r'"\s*:\s*(".*?"|[\[{].*?[\]}]|[^,}\]]+)'
            matches = re.search(pattern, text, re.DOTALL)
            if matches:
                value_str = matches.group(1).strip()
                try:
                    # Try to parse as JSON with proper syntax
                    if value_str.startswith('"') and value_str.endswith('"'):
                        # String value
                        result[name] = json.loads(value_str)
                    elif value_str.startswith('[') and value_str.endswith(']'):
                        # List value
                        result[name] = json.loads(value_str)
                    elif value_str.startswith('{') and value_str.endswith('}'):
                        # Dict value
                        result[name] = json.loads(value_str)
                    else:
                        # Simple value - handle as string
                        result[name] = value_str
                except json.JSONDecodeError:
                    # Just use the string value without quotes
                    result[name] = value_str.strip('"')

        return result


# Global instance
semantic_understanding = SemanticUnderstanding()
