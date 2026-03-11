"""Photo Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PhotoBase(BaseModel):
    """Base photo schema with common fields."""

    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    tags: list[str] = []


class PhotoCreate(PhotoBase):
    """Schema for photo creation."""

    album_id: int | None = None


class PhotoUpdate(BaseModel):
    """Schema for photo update."""

    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    album_id: int | None = None
    tags: list[str] | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class PhotoInDB(PhotoBase):
    """Schema for photo data from database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    album_id: int | None
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    width: int | None
    height: int | None
    taken_at: datetime | None
    latitude: float | None
    longitude: float | None
    altitude: float | None
    is_processed: bool
    is_indexed: bool
    thumbnail_small: str | None
    thumbnail_medium: str | None
    railway_station_code: str | None
    railway_station_name: str | None
    train_number: str | None
    created_at: datetime
    updated_at: datetime


class PhotoWithEXIF(PhotoInDB):
    """Photo schema with EXIF data."""

    exif_data: dict[str, Any] | None = None


class PhotoWithOCR(PhotoInDB):
    """Photo schema with OCR results."""

    ocr_text: str | None
    ocr_confidence: float | None
    ticket_data: dict[str, Any] | None


class PhotoUploadResponse(BaseModel):
    """Response schema for photo upload."""

    success: bool
    photo: PhotoInDB | None
    error: str | None


class PhotoBatchUpload(BaseModel):
    """Schema for batch photo upload."""

    album_id: int | None = None
    photos: list[PhotoCreate]


class PhotoFilter(BaseModel):
    """Filter options for photo queries."""

    album_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    tags: list[str] | None = None
    has_location: bool | None = None
    is_processed: bool | None = None
    railway_station_code: str | None = None
    search_query: str | None = None


class PhotoMapItem(BaseModel):
    """Lightweight photo item for map display."""

    id: int
    latitude: float
    longitude: float
    thumbnail_small: str | None
    taken_at: datetime | None
