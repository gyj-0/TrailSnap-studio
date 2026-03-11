"""Photo CRUD operations."""

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.photo import Photo
from app.schemas.photo import PhotoCreate, PhotoFilter, PhotoUpdate

from .base import CRUDBase


class CRUDPhoto(CRUDBase[Photo, PhotoCreate, PhotoUpdate]):
    """CRUD operations for Photo model."""

    async def get_with_exif(self, db: AsyncSession, *, id: int) -> Photo | None:
        """Get photo with EXIF data."""
        result = await db.execute(
            select(Photo).where(Photo.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Photo]:
        """Get photos by owner."""
        result = await db.execute(
            select(Photo)
            .where(Photo.owner_id == owner_id)
            .order_by(desc(Photo.taken_at), desc(Photo.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_album(
        self,
        db: AsyncSession,
        *,
        album_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Photo]:
        """Get photos by album."""
        result = await db.execute(
            select(Photo)
            .where(Photo.album_id == album_id)
            .order_by(desc(Photo.taken_at), desc(Photo.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_checksum(
        self,
        db: AsyncSession,
        *,
        checksum: str,
        owner_id: int | None = None,
    ) -> Photo | None:
        """Get photo by checksum (for deduplication)."""
        query = select(Photo).where(Photo.checksum == checksum)
        if owner_id:
            query = query.where(Photo.owner_id == owner_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search_photos(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        filters: PhotoFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Photo], int]:
        """Search photos with filters. Returns (photos, total_count)."""
        query = select(Photo).where(Photo.owner_id == owner_id)
        count_query = select(func.count(Photo.id)).where(Photo.owner_id == owner_id)

        # Apply filters
        if filters.album_id is not None:
            query = query.where(Photo.album_id == filters.album_id)
            count_query = count_query.where(Photo.album_id == filters.album_id)

        if filters.start_date:
            query = query.where(Photo.taken_at >= filters.start_date)
            count_query = count_query.where(Photo.taken_at >= filters.start_date)

        if filters.end_date:
            query = query.where(Photo.taken_at <= filters.end_date)
            count_query = count_query.where(Photo.taken_at <= filters.end_date)

        if filters.has_location is True:
            query = query.where(
                Photo.latitude.is_not(None), Photo.longitude.is_not(None)
            )
            count_query = count_query.where(
                Photo.latitude.is_not(None), Photo.longitude.is_not(None)
            )
        elif filters.has_location is False:
            query = query.where(
                Photo.latitude.is_(None), Photo.longitude.is_(None)
            )
            count_query = count_query.where(
                Photo.latitude.is_(None), Photo.longitude.is_(None)
            )

        if filters.is_processed is not None:
            query = query.where(Photo.is_processed == filters.is_processed)
            count_query = count_query.where(Photo.is_processed == filters.is_processed)

        if filters.railway_station_code:
            query = query.where(
                Photo.railway_station_code == filters.railway_station_code
            )
            count_query = count_query.where(
                Photo.railway_station_code == filters.railway_station_code
            )

        # Execute count query
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Execute main query with pagination
        query = query.order_by(desc(Photo.taken_at), desc(Photo.created_at))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        photos = list(result.scalars().all())

        return photos, total

    async def get_map_photos(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        bounds: dict[str, float] | None = None,
    ) -> list[Photo]:
        """Get photos with location data for map display."""
        query = (
            select(Photo)
            .where(Photo.owner_id == owner_id)
            .where(Photo.latitude.is_not(None))
            .where(Photo.longitude.is_not(None))
        )

        if bounds:
            query = query.where(
                Photo.latitude >= bounds.get("south", -90),
                Photo.latitude <= bounds.get("north", 90),
                Photo.longitude >= bounds.get("west", -180),
                Photo.longitude <= bounds.get("east", 180),
            )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: PhotoCreate,
        extra_data: dict[str, Any] | None = None,
    ) -> Photo:
        """Create new photo record."""
        db_obj = Photo(
            title=obj_in.title,
            description=obj_in.description,
            tags=obj_in.tags or [],
            album_id=obj_in.album_id,
            owner_id=extra_data.get("owner_id") if extra_data else None,
        )
        if extra_data:
            for field, value in extra_data.items():
                if field not in ("owner_id",):
                    setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update_processing_status(
        self,
        db: AsyncSession,
        *,
        photo_id: int,
        is_processed: bool = True,
        error: str | None = None,
    ) -> Photo:
        """Update photo processing status."""
        photo = await self.get(db, photo_id)
        if photo:
            photo.is_processed = is_processed
            if error:
                photo.processing_error = error
            db.add(photo)
            await db.flush()
            await db.refresh(photo)
        return photo

    async def update_ocr_result(
        self,
        db: AsyncSession,
        *,
        photo_id: int,
        ocr_text: str | None,
        ocr_confidence: float | None,
        ticket_data: dict | None,
    ) -> Photo:
        """Update OCR results for photo."""
        photo = await self.get(db, photo_id)
        if photo:
            photo.ocr_text = ocr_text
            photo.ocr_confidence = ocr_confidence
            photo.ticket_data = ticket_data
            db.add(photo)
            await db.flush()
            await db.refresh(photo)
        return photo


photo = CRUDPhoto(Photo)
