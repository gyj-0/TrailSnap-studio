"""API v1 routes."""

from fastapi import APIRouter

from .album import router as album_router
from .photo import router as photo_router
from .system import router as system_router
from .user import router as user_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(album_router, prefix="/albums", tags=["albums"])
api_router.include_router(photo_router, prefix="/photos", tags=["photos"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
