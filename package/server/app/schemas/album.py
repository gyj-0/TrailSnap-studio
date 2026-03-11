"""Album Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlbumBase(BaseModel):
    """Base album schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    location: str | None = Field(None, max_length=200)
    is_public: bool = False


class AlbumCreate(AlbumBase):
    """Schema for album creation."""

    parent_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class AlbumUpdate(BaseModel):
    """Schema for album update."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    cover_photo_id: int | None = None
    location: str | None = Field(None, max_length=200)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_public: bool | None = None
    parent_id: int | None = None


class AlbumInDB(AlbumBase):
    """Schema for album data from database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    parent_id: int | None
    cover_photo_id: int | None
    photo_count: int
    total_size: int
    start_date: datetime | None
    end_date: datetime | None
    created_at: datetime
    updated_at: datetime


class AlbumSummary(BaseModel):
    """Lightweight album summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    cover_photo_id: int | None
    photo_count: int
    created_at: datetime


class AlbumWithPhotos(AlbumInDB):
    """Album schema with nested photos."""

    photos: list["PhotoSummary"] = []  # type: ignore  # noqa: F821
    children: list["AlbumSummary"] = []  # type: ignore  # noqa: F821


class PhotoSummary(BaseModel):
    """Lightweight photo summary for album view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    thumbnail_small: str | None
    taken_at: datetime | None
    latitude: float | None
    longitude: float | None
