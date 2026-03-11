"""Album API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.security import get_current_user_id
from app.crud import album as album_crud
from app.db.session import get_db
from app.schemas.album import AlbumCreate, AlbumInDB, AlbumSummary, AlbumUpdate, AlbumWithPhotos
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=PaginatedResponse[AlbumSummary])
async def list_albums(
    *,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    root_only: bool = Query(False, description="Only return root albums"),
) -> PaginatedResponse[AlbumSummary]:
    """List user's albums."""
    user_id = int(current_user_id)
    
    if root_only:
        albums = await album_crud.get_root_albums(db, owner_id=user_id, skip=skip, limit=limit)
        total = len(albums)  # TODO: Implement proper count
    else:
        albums = await album_crud.get_by_owner(db, owner_id=user_id, skip=skip, limit=limit)
        total = len(albums)  # TODO: Implement proper count
    
    album_summaries = [AlbumSummary.model_validate(a) for a in albums]
    
    return PaginatedResponse(
        data=album_summaries,
        meta=PaginationMeta(
            page=skip // limit + 1,
            page_size=limit,
            total=total,
            total_pages=(total + limit - 1) // limit,
            has_next=skip + limit < total,
            has_prev=skip > 0,
        ),
    )


@router.post("", response_model=AlbumInDB, status_code=status.HTTP_201_CREATED)
async def create_album(
    *,
    db: AsyncSession = Depends(get_db),
    album_in: AlbumCreate,
    current_user_id: str = Depends(get_current_user_id),
) -> AlbumInDB:
    """Create a new album."""
    user_id = int(current_user_id)
    
    # Validate parent_id if provided
    if album_in.parent_id:
        parent = await album_crud.get(db, id=album_in.parent_id)
        if not parent or parent.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parent album",
            )
    
    album = await album_crud.create(
        db, obj_in=album_in, extra_data={"owner_id": user_id}
    )
    logger.info(f"Album created: {album.title} by user {user_id}")
    return AlbumInDB.model_validate(album)


@router.get("/{album_id}", response_model=AlbumWithPhotos)
async def get_album(
    *,
    db: AsyncSession = Depends(get_db),
    album_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> AlbumWithPhotos:
    """Get album details with photos."""
    user_id = int(current_user_id)
    
    album = await album_crud.get_with_photos(db, id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    
    if album.owner_id != user_id and not album.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return AlbumWithPhotos.model_validate(album)


@router.put("/{album_id}", response_model=AlbumInDB)
async def update_album(
    *,
    db: AsyncSession = Depends(get_db),
    album_id: int,
    album_in: AlbumUpdate,
    current_user_id: str = Depends(get_current_user_id),
) -> AlbumInDB:
    """Update an album."""
    user_id = int(current_user_id)
    
    album = await album_crud.get(db, id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    
    if album.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Validate new parent_id if provided
    if album_in.parent_id is not None:
        if album_in.parent_id == album_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Album cannot be its own parent",
            )
        parent = await album_crud.get(db, id=album_in.parent_id)
        if parent and parent.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parent album",
            )
    
    album = await album_crud.update(db, db_obj=album, obj_in=album_in)
    logger.info(f"Album updated: {album_id}")
    return AlbumInDB.model_validate(album)


@router.delete("/{album_id}", response_model=SuccessResponse)
async def delete_album(
    *,
    db: AsyncSession = Depends(get_db),
    album_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> SuccessResponse:
    """Delete an album."""
    user_id = int(current_user_id)
    
    album = await album_crud.get(db, id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    
    if album.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    await album_crud.delete(db, id=album_id)
    logger.info(f"Album deleted: {album_id}")
    return SuccessResponse(message="Album deleted successfully")


@router.get("/{album_id}/children", response_model=list[AlbumSummary])
async def get_album_children(
    *,
    db: AsyncSession = Depends(get_db),
    album_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> list[AlbumSummary]:
    """Get child albums."""
    user_id = int(current_user_id)
    
    album = await album_crud.get(db, id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    
    if album.owner_id != user_id and not album.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    children = await album_crud.get_children(db, parent_id=album_id)
    return [AlbumSummary.model_validate(c) for c in children]
