"""User Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.config import settings


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    nickname: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v[0].isalnum():
            raise ValueError("Username must start with a letter or number")
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for user update."""

    nickname: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)


class UserInDB(UserBase):
    """Schema for user data from database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime


class UserResponse(UserBase):
    """Schema for user response (public data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar_url: str | None
    created_at: datetime


class UserProfile(UserResponse):
    """Schema for detailed user profile."""

    bio: str | None
    album_count: int = 0
    photo_count: int = 0


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset."""

    token: str
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)
