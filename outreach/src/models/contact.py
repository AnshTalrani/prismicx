from typing import List, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Contact(BaseModel):
    id: str
    name: str
    # Add additional fields as needed (email, phone, etc.)

class ContactList(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    contacts: List[Contact]
    metadata: Dict[str, Any] = Field(default_factory=dict)
