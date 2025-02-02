from ..models.execution_status import ExecutionStatus
from typing import Any, Dict
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class Request(BaseModel):
    request_id: UUID = Field(default_factory=uuid4, description="Unique identifier for the request")
    user_id: str = Field(..., description="Identifier for the user making the request")
    purpose_id: str = Field(..., description="Identifier for the purpose of the request")
    context: Dict[str, Any] = Field(default_factory=dict, description="Contextual data for the request")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Current status of the request")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp of the request")

    def add_context(self, key: str, value: Any) -> None:
        """
        Adds a key-value pair to the request context.
        """
        self.context[key] = value

    def get_context(self, key: str) -> Any:
        """
        Retrieves a value from the request context by key.
        """
        return self.context.get(key) 