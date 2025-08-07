"""
Contact Repository

This module provides database access operations for contacts,
extending the base repository with contact-specific queries.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.database import Contact
from src.repositories.base import BaseRepository
from src.models.schemas import BaseSchema

class ContactCreate(BaseSchema):
    """Schema for creating a new contact."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ContactUpdate(ContactCreate):
    """Schema for updating an existing contact."""
    pass

class ContactRepository(BaseRepository[Contact, ContactCreate, ContactUpdate]):
    """Repository for contact database operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        super().__init__(Contact, db_session)
    
    async def get_by_email(self, email: str) -> Optional[Contact]:
        """Retrieve a contact by email."""
        if not email:
            return None
            
        result = await self.db.execute(
            select(Contact).where(Contact.email == email)
        )
        return result.scalars().first()
    
    async def get_by_phone(self, phone: str) -> Optional[Contact]:
        """Retrieve a contact by phone number."""
        if not phone:
            return None
            
        result = await self.db.execute(
            select(Contact).where(Contact.phone == phone)
        )
        return result.scalars().first()
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Contact]:
        """Search contacts by name, email, or phone."""
        if not query or len(query.strip()) < 2:
            return []
            
        search = f"%{query}%"
        
        result = await self.db.execute(
            select(Contact).where(
                or_(
                    Contact.first_name.ilike(search),
                    Contact.last_name.ilike(search),
                    Contact.email.ilike(search),
                    Contact.phone.ilike(search)
                )
            )
            .order_by(Contact.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def upsert_by_email(
        self,
        contact_data: ContactCreate
    ) -> Contact:
        """Create or update a contact by email."""
        if not contact_data.email:
            raise ValueError("Email is required for upsert operation")
            
        # Try to find existing contact
        existing = await self.get_by_email(contact_data.email)
        
        if existing:
            # Update existing contact
            return await self.update(db_obj=existing, obj_in=contact_data)
        else:
            # Create new contact
            return await self.create(contact_data)
    
    async def get_or_create(
        self,
        email: str,
        **kwargs
    ) -> Contact:
        """Get an existing contact by email or create a new one."""
        contact = await self.get_by_email(email)
        if contact:
            return contact
            
        # Create new contact with provided data
        contact_data = {
            "email": email,
            **kwargs
        }
        return await self.create(contact_data)
