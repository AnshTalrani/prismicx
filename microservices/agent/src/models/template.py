"""
Simplified template structure for execution flows
"""
from pydantic import BaseModel, Field
from typing import List, Dict

class ProcessingStep(BaseModel):
    service: str = Field(..., example="content-generator")
    operation: str = Field(..., example="generate_product_description")
    input_map: Dict[str, str] = Field(
        {"product_name": "item.product", "category": "user.category"},
        description="Context to service input mapping"
    )
    output_map: Dict[str, str] = Field(
        {"description": "generated_text"},
        description="Service output to context mapping"
    )
    retry_policy: Dict[str, any] = {
        "max_attempts": 3,
        "retriable_errors": ["TimeoutError", "ConnectionError"]
    }

class ExecutionTemplate(BaseModel):
    id: str
    description: str
    processing_mode: str = "realtime"  # realtime/batch
    steps: List[ProcessingStep]
    batch_config: Dict[str, any] = {
        "chunk_size": 100,
        "max_parallel": 5,
        "timeout": 3600,
        "result_aggregation": "full/partial"
    }

class ServiceSequenceTemplate(BaseModel):
    sequence_id: str
    description: str
    steps: list[ProcessingStep]
    batch_defaults: dict = {
        "chunk_size": 100,
        "max_parallel": 5,
        "timeout": 3600
    } 