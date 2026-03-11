"""CRUD operations package."""

from .album import album
from .base import CRUDBase
from .photo import photo
from .user import user

__all__ = ["CRUDBase", "user", "album", "photo"]
