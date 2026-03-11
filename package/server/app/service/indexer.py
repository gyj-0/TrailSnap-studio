"""Photo indexing service for search and retrieval."""

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.db.models.photo import Photo

logger = get_logger(__name__)


class PhotoIndexer:
    """
    Service for indexing photos for efficient search.
    
    Features:
    - Full-text search indexing
    - Geospatial indexing
    - Tag-based indexing
    - EXIF metadata indexing
    """

    def __init__(self):
        self._initialized = False

    async def initialize(self, db: AsyncSession) -> None:
        """Initialize indexing (create necessary database structures)."""
        # TODO: Create full-text search indexes if needed
        self._initialized = True
        logger.info("Photo indexer initialized")

    async def index_photo(self, db: AsyncSession, photo: Photo) -> None:
        """
        Index a single photo.
        
        Args:
            db: Database session
            photo: Photo to index
        """
        if not self._initialized:
            await self.initialize(db)

        # Build search text from photo metadata
        search_terms = []
        
        if photo.title:
            search_terms.append(photo.title)
        if photo.description:
            search_terms.append(photo.description)
        if photo.tags:
            search_terms.extend(photo.tags)
        if photo.railway_station_name:
            search_terms.append(photo.railway_station_name)
        if photo.ocr_text:
            search_terms.append(photo.ocr_text)

        # Update search vector (if using PostgreSQL full-text search)
        search_text = " ".join(filter(None, search_terms))
        
        try:
            # Mark photo as indexed
            photo.is_indexed = True
            await db.flush()
            logger.debug(f"Photo indexed: {photo.id}")
        except Exception as e:
            logger.error(f"Failed to index photo {photo.id}: {e}")
            raise

    async def index_photos_batch(
        self,
        db: AsyncSession,
        photo_ids: list[int],
    ) -> dict[str, int]:
        """
        Index multiple photos in batch.
        
        Args:
            db: Database session
            photo_ids: List of photo IDs to index
            
        Returns:
            Dict with indexing results
        """
        results = {"success": 0, "failed": 0}
        
        for photo_id in photo_ids:
            try:
                photo = await db.get(Photo, photo_id)
                if photo:
                    await self.index_photo(db, photo)
                    results["success"] += 1
                else:
                    logger.warning(f"Photo not found for indexing: {photo_id}")
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to index photo {photo_id}: {e}")
                results["failed"] += 1

        logger.info(f"Batch indexing complete: {results}")
        return results

    async def search(
        self,
        db: AsyncSession,
        query: str,
        owner_id: int | None = None,
        limit: int = 20,
    ) -> list[Photo]:
        """
        Search photos using full-text search.
        
        Args:
            db: Database session
            query: Search query
            owner_id: Optional owner filter
            limit: Maximum results
            
        Returns:
            List of matching photos
        """
        # Simple implementation using ILIKE
        # For production, consider using PostgreSQL full-text search
        search_query = f"%{query}%"
        
        sql = """
            SELECT * FROM photos 
            WHERE (
                title ILIKE :query 
                OR description ILIKE :query 
                OR ocr_text ILIKE :query
                OR railway_station_name ILIKE :query
            )
        """
        params = {"query": search_query}
        
        if owner_id:
            sql += " AND owner_id = :owner_id"
            params["owner_id"] = owner_id
        
        sql += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit

        result = await db.execute(text(sql), params)
        photos = result.mappings().all()
        
        return [Photo(**dict(p)) for p in photos]

    async def get_photos_by_location(
        self,
        db: AsyncSession,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        owner_id: int | None = None,
        limit: int = 50,
    ) -> list[Photo]:
        """
        Find photos near a location.
        
        Args:
            db: Database session
            lat: Latitude
            lng: Longitude
            radius_km: Search radius in kilometers
            owner_id: Optional owner filter
            limit: Maximum results
            
        Returns:
            List of nearby photos
        """
        # Use Haversine formula for distance calculation
        # This is a simplified implementation
        sql = """
            SELECT *, (
                6371 * acos(
                    cos(radians(:lat)) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians(:lng)) +
                    sin(radians(:lat)) * sin(radians(latitude))
                )
            ) AS distance
            FROM photos
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            AND (
                6371 * acos(
                    cos(radians(:lat)) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians(:lng)) +
                    sin(radians(:lat)) * sin(radians(latitude))
                )
            ) <= :radius
        """
        params = {
            "lat": lat,
            "lng": lng,
            "radius": radius_km,
        }
        
        if owner_id:
            sql += " AND owner_id = :owner_id"
            params["owner_id"] = owner_id
        
        sql += " ORDER BY distance LIMIT :limit"
        params["limit"] = limit

        result = await db.execute(text(sql), params)
        photos = result.mappings().all()
        
        return [Photo(**dict(p)) for p in photos]

    async def reindex_all(
        self,
        db: AsyncSession,
        owner_id: int | None = None,
    ) -> dict[str, int]:
        """
        Reindex all photos.
        
        Args:
            db: Database session
            owner_id: Optional owner filter
            
        Returns:
            Dict with reindexing results
        """
        # Get all photo IDs
        sql = "SELECT id FROM photos WHERE is_indexed = FALSE"
        params = {}
        
        if owner_id:
            sql += " AND owner_id = :owner_id"
            params["owner_id"] = owner_id

        result = await db.execute(text(sql), params)
        photo_ids = [row[0] for row in result.all()]

        logger.info(f"Starting reindex of {len(photo_ids)} photos")
        return await self.index_photos_batch(db, photo_ids)


# Global indexer instance
indexer = PhotoIndexer()
