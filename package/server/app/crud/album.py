"""Album CRUD operations."""

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.album import Album
from app.schemas.album import AlbumCreate, AlbumUpdate

from .base import CRUDBase


class CRUDAlbum(CRUDBase[Album, AlbumCreate, AlbumUpdate]):
    """CRUD operations for Album model."""

    async def get_with_photos(
        self,
        db: AsyncSession,
        *,
        id: int,
    ) -> Album | None:
        """Get album with photos loaded."""
        result = await db.execute(
            select(Album)
            .where(Album.id == id)
            .options(selectinload(Album.photos))
            .options(selectinload(Album.children))
        )
        return result.scalar_one_or_none()

    async def get_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Album]:
        """Get albums by owner."""
        result = await db.execute(
            select(Album)
            .where(Album.owner_id == owner_id)
            .order_by(desc(Album.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_root_albums(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Album]:
        """Get root albums (no parent) for owner."""
        result = await db.execute(
            select(Album)
            .where(Album.owner_id == owner_id)
            .where(Album.parent_id.is_(None))
            .order_by(desc(Album.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_children(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
    ) -> list[Album]:
        """Get child albums."""
        result = await db.execute(
            select(Album)
            .where(Album.parent_id == parent_id)
            .order_by(Album.title)
        )
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: AlbumCreate,
        extra_data: dict[str, Any] | None = None,
    ) -> Album:
        """Create new album."""
        db_obj = Album(
            title=obj_in.title,
            description=obj_in.description,
            location=obj_in.location,
            is_public=obj_in.is_public,
            owner_id=extra_data.get("owner_id") if extra_data else None,
            parent_id=obj_in.parent_id,
            start_date=obj_in.start_date,
            end_date=obj_in.end_date,
        )
        if extra_data:
            for field, value in extra_data.items():
                if field != "owner_id":
                    setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update_photo_count(
        self,
        db: AsyncSession,
        *,
        album_id: int,
        count: int | None = None,
    ) -> None:
        """Update album photo count. If count is None, recalculate from photos."""
        album = await self.get(db, album_id)
        if album:
            if count is None:
                from app.db.models.photo import Photo
                result = await db.execute(
                    select(Photo).where(Photo.album_id == album_id)
                )
                count = len(result.scalars().all())
            album.photo_count = count
            db.add(album)
            await db.flush()


album = CRUDAlbum(Album)
