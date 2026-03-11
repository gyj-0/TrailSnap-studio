"""Photo API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.security import get_current_user_id
from app.crud import photo as photo_crud
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.photo import PhotoCreate, PhotoFilter, PhotoInDB, PhotoMapItem, PhotoUpdate

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=PaginatedResponse[PhotoInDB])
async def list_photos(
    *,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    album_id: int | None = None,
) -> PaginatedResponse[PhotoInDB]:
    """List user's photos."""
    user_id = int(current_user_id)
    
    filters = PhotoFilter(album_id=album_id)
    photos, total = await photo_crud.search_photos(
        db, owner_id=user_id, filters=filters, skip=skip, limit=limit
    )
    
    return PaginatedResponse(
        data=[PhotoInDB.model_validate(p) for p in photos],
        meta=PaginationMeta(
            page=skip // limit + 1,
            page_size=limit,
            total=total,
            total_pages=(total + limit - 1) // limit,
            has_next=skip + limit < total,
            has_prev=skip > 0,
        ),
    )


@router.post("", response_model=PhotoInDB, status_code=status.HTTP_201_CREATED)
async def create_photo(
    *,
    db: AsyncSession = Depends(get_db),
    photo_in: PhotoCreate,
    current_user_id: str = Depends(get_current_user_id),
) -> PhotoInDB:
    """Create a new photo record (metadata only)."""
    user_id = int(current_user_id)
    
    photo = await photo_crud.create(
        db, obj_in=photo_in, extra_data={"owner_id": user_id}
    )
    logger.info(f"Photo created: {photo.id} by user {user_id}")
    return PhotoInDB.model_validate(photo)


@router.post("/upload", response_model=SuccessResponse)
async def upload_photo(
    *,
    db: AsyncSession = Depends(get_db),
    file: UploadFile,
    album_id: int | None = None,
    current_user_id: str = Depends(get_current_user_id),
) -> SuccessResponse:
    """Upload a photo file."""
    user_id = int(current_user_id)
    
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )
    
    # TODO: Implement file upload logic
    # - Save file to storage
    # - Extract EXIF data
    # - Generate thumbnails
    # - Create photo record
    
    logger.info(f"Photo uploaded by user {user_id}: {file.filename}")
    return SuccessResponse(
        message="Photo uploaded successfully",
        data={"filename": file.filename, "album_id": album_id},
    )


@router.get("/search", response_model=PaginatedResponse[PhotoInDB])
async def search_photos(
    *,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    filters: PhotoFilter = Depends(),
) -> PaginatedResponse[PhotoInDB]:
    """Search photos with filters."""
    user_id = int(current_user_id)
    
    photos, total = await photo_crud.search_photos(
        db, owner_id=user_id, filters=filters, skip=skip, limit=limit
    )
    
    return PaginatedResponse(
        data=[PhotoInDB.model_validate(p) for p in photos],
        meta=PaginationMeta(
            page=skip // limit + 1,
            page_size=limit,
            total=total,
            total_pages=(total + limit - 1) // limit,
            has_next=skip + limit < total,
            has_prev=skip > 0,
        ),
    )


@router.get("/map", response_model=list[PhotoMapItem])
async def get_map_photos(
    *,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    north: float | None = None,
    south: float | None = None,
    east: float | None = None,
    west: float | None = None,
) -> list[PhotoMapItem]:
    """Get photos with location data for map display."""
    user_id = int(current_user_id)
    
    bounds = None
    if all(v is not None for v in [north, south, east, west]):
        bounds = {"north": north, "south": south, "east": east, "west": west}
    
    photos = await photo_crud.get_map_photos(db, owner_id=user_id, bounds=bounds)
    return [PhotoMapItem.model_validate(p) for p in photos]


@router.get("/{photo_id}", response_model=PhotoInDB)
async def get_photo(
    *,
    db: AsyncSession = Depends(get_db),
    photo_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> PhotoInDB:
    """Get photo details."""
    user_id = int(current_user_id)
    
    photo = await photo_crud.get(db, id=photo_id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    if photo.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return PhotoInDB.model_validate(photo)


@router.put("/{photo_id}", response_model=PhotoInDB)
async def update_photo(
    *,
    db: AsyncSession = Depends(get_db),
    photo_id: int,
    photo_in: PhotoUpdate,
    current_user_id: str = Depends(get_current_user_id),
) -> PhotoInDB:
    """Update a photo."""
    user_id = int(current_user_id)
    
    photo = await photo_crud.get(db, id=photo_id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    if photo.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    photo = await photo_crud.update(db, db_obj=photo, obj_in=photo_in)
    logger.info(f"Photo updated: {photo_id}")
    return PhotoInDB.model_validate(photo)


@router.delete("/{photo_id}", response_model=SuccessResponse)
async def delete_photo(
    *,
    db: AsyncSession = Depends(get_db),
    photo_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> SuccessResponse:
    """Delete a photo."""
    user_id = int(current_user_id)
    
    photo = await photo_crud.get(db, id=photo_id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    if photo.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # TODO: Delete file from storage
    await photo_crud.delete(db, id=photo_id)
    logger.info(f"Photo deleted: {photo_id}")
    return SuccessResponse(message="Photo deleted successfully")
