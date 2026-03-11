"""Pydantic schemas package."""

from .album import AlbumCreate, AlbumInDB, AlbumUpdate, AlbumWithPhotos
from .common import ErrorResponse, PaginatedResponse, SuccessResponse
from .photo import PhotoCreate, PhotoInDB, PhotoUpdate, PhotoWithEXIF
from .user import UserCreate, UserInDB, UserLogin, UserResponse, UserUpdate

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    "UserLogin",
    # Album schemas
    "AlbumCreate",
    "AlbumUpdate",
    "AlbumInDB",
    "AlbumWithPhotos",
    # Photo schemas
    "PhotoCreate",
    "PhotoUpdate",
    "PhotoInDB",
    "PhotoWithEXIF",
    # Common schemas
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
]
