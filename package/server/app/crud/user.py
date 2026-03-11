"""User CRUD operations."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate

from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> User | None:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def authenticate(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
    ) -> User | None:
        """
        Authenticate user with username/email and password.
        
        Returns:
            User if authenticated, None otherwise
        """
        # Try username first, then email
        user = await self.get_by_username(db, username=username)
        if not user:
            user = await self.get_by_email(db, email=username)
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: UserCreate,
        extra_data: dict[str, Any] | None = None,
    ) -> User:
        """Create new user with hashed password."""
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            nickname=obj_in.nickname,
            bio=obj_in.bio,
        )
        if extra_data:
            for field, value in extra_data.items():
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update_password(
        self,
        db: AsyncSession,
        *,
        user: User,
        new_password: str,
    ) -> User:
        """Update user password."""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    async def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser


user = CRUDUser(User)
