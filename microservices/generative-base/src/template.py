"""
Central Template class representing the processing pipeline state.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from redis import Redis

class Template:
    """
    Main data structure for processing pipeline state management
    
    Attributes:
        purpose_id: Unique identifier for the processing purpose
        context: Dictionary of contextual information
        user_details: Extracted user information
        extracted_data: Raw data from various sources
        selected_info: Curated/processed information
        generated_output: Final output structure
    """
    
    def __init__(self, purpose_id: str):
        self.purpose_id = purpose_id
        self.context: Dict[str, Any] = {}
        self.user_details: Dict[str, Any] = {}
        self.extracted_data: Dict[str, Any] = {}
        self.selected_info: Dict[str, Any] = {}
        self.generated_output: Dict[str, Any] = {}
        self._validate_intent_tag()
    
    def _validate_intent_tag(self):
        """Ensure valid intent tag exists in selected_info"""
        valid_tags = {"pre", "pro", "post"}
        if "intent_tag" not in self.selected_info:
            self.selected_info["intent_tag"] = "post"
        elif self.selected_info["intent_tag"] not in valid_tags:
            raise ValueError(f"Invalid intent tag: {self.selected_info['intent_tag']}")
    
    def validate(self) -> bool:
        """Validate template state before processing"""
        required_fields = ['purpose_id', 'context', 'user_details']
        return all(getattr(self, field) for field in required_fields)

class ValidatedTemplate(BaseModel):
    id: str
    steps: List[ProcessingStep]
    hash: str  # Content hash for duplicate checking

class TemplateStore:
    def __init__(self):
        self.redis = Redis(host='redis', port=6379, db=1)  # Different DB than agent
    
    def store(self, template: ValidatedTemplate):
        """Store with 1h TTL for batch processing"""
        self.redis.setex(
            f"gen_template:{template.hash}",
            3600,
            template.json()
        )
    
    def retrieve(self, template_hash: str) -> Optional[ValidatedTemplate]:
        data = self.redis.get(f"gen_template:{template_hash}")
        return ValidatedTemplate.parse_raw(data) if data else None 