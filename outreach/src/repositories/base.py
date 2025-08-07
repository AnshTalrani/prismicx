"""
Base Repository

This module provides a base repository class with common CRUD operations
that can be inherited by specific repository implementations.
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=Any)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=Any)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with default CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        """Initialize with database session and model class."""
        self.model = model
        self.db = db_session
    
    async def get(self, id: Union[UUID, str]) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()
    
    async def list(
        self, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        **filters: Any
    ) -> List[ModelType]:
        """List records with optional filtering and pagination."""
        stmt = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in.dict() if hasattr(obj_in, 'dict') else obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        *, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record."""
        obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: Union[UUID, str]) -> bool:
        """Delete a record by ID."""
        obj = await self.get(id)
        if not obj:
            return False
            
        await self.db.delete(obj)
        await self.db.commit()
        return True
