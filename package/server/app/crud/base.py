"""Base CRUD class with common database operations."""

from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.
    
    Provides generic implementations for common database operations.
    """

    def __init__(self, model: type[ModelType]):
        """
        Initialize with SQLAlchemy model class.
        
        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            The record if found, None otherwise
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: Any) -> ModelType:
        """
        Get a single record by ID or raise 404.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            The record
            
        Raises:
            HTTPException: If record not found
        """
        obj = await self.get(db, id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {id} not found",
            )
        return obj

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        extra_data: dict[str, Any] | None = None,
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic schema with create data
            extra_data: Additional data to include
            
        Returns:
            Created record
        """
        obj_data = obj_in.model_dump()
        if extra_data:
            obj_data.update(extra_data)
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Existing database object
            obj_in: Pydantic schema or dict with update data
            
        Returns:
            Updated record
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> ModelType:
        """
        Delete a record.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Deleted record
        """
        obj = await self.get_or_404(db, id)
        await db.delete(obj)
        await db.flush()
        return obj

    async def count(self, db: AsyncSession) -> int:
        """
        Count total records.
        
        Args:
            db: Database session
            
        Returns:
            Total count
        """
        from sqlalchemy import func
        result = await db.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def exists(self, db: AsyncSession, id: Any) -> bool:
        """
        Check if record exists.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            True if exists, False otherwise
        """
        result = await db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
