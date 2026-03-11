"""User API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user_id,
)
from app.crud import user as user_crud
from app.db.session import get_db
from app.schemas.common import SuccessResponse, TokenData
from app.schemas.user import (
    PasswordChange,
    UserCreate,
    UserInDB,
    UserLogin,
    UserProfile,
    UserResponse,
    UserUpdate,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> UserResponse:
    """Register a new user."""
    # Check if username exists
    existing_user = await user_crud.get_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email exists
    existing_user = await user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = await user_crud.create(db, obj_in=user_in)
    logger.info(f"User registered: {user.username}")
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenData)
async def login(
    *,
    db: AsyncSession = Depends(get_db),
    credentials: UserLogin,
) -> TokenData:
    """Authenticate user and return tokens."""
    user = await user_crud.authenticate(
        db, username=credentials.username, password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    logger.info(f"User logged in: {user.username}")
    return TokenData(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    *,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> UserResponse:
    """Get current user profile."""
    user = await user_crud.get(db, id=int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
) -> UserResponse:
    """Update current user profile."""
    user = await user_crud.get(db, id=int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user = await user_crud.update(db, db_obj=user, obj_in=user_in)
    logger.info(f"User updated: {user.username}")
    return UserResponse.model_validate(user)


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    *,
    db: AsyncSession = Depends(get_db),
    password_data: PasswordChange,
    current_user_id: str = Depends(get_current_user_id),
) -> SuccessResponse:
    """Change user password."""
    user = await user_crud.get(db, id=int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify current password
    from app.core.security import verify_password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    await user_crud.update_password(db, user=user, new_password=password_data.new_password)
    logger.info(f"Password changed for user: {user.username}")
    return SuccessResponse(message="Password changed successfully")


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
) -> UserProfile:
    """Get public profile of a user."""
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    profile = UserProfile.model_validate(user)
    # TODO: Calculate album_count and photo_count
    profile.album_count = 0
    profile.photo_count = 0
    
    return profile
