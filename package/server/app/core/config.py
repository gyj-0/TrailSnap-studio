"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import PostgresDsn, computed_field, field_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TRAILSNAP_",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "TrailSnap"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    # Database
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "trailsnap"
    DATABASE_PASSWORD: str = "trailsnap"
    DATABASE_NAME: str = "trailsnap"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    PASSWORD_MIN_LENGTH: int = 8

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_DIR: Path = Path("logs")
    LOG_MAX_BYTES_PER_DAY: int = 100 * 1024 * 1024  # 100MB per day
    LOG_BACKUP_DAYS: int = 30

    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/heic"}

    # Railway Data Sync
    RAILWAY_SYNC_INTERVAL_MINUTES: int = 60
    RAILWAY_API_BASE_URL: str = "https://api.example.com/railway"

    # OCR/YOLO
    YOLO_MODEL_PATH: Path = Path("models/yolo")
    OCR_MODEL_PATH: Path = Path("models/ocr")
    OCR_CONFIDENCE_THRESHOLD: float = 0.5

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("CORS_METHODS", mode="before")
    @classmethod
    def parse_cors_methods(cls, value: Any) -> list[str]:
        """Parse CORS methods from string or list."""
        if isinstance(value, str):
            return [method.strip() for method in value.split(",") if method.strip()]
        return value

    @field_validator("CORS_HEADERS", mode="before")
    @classmethod
    def parse_cors_headers(cls, value: Any) -> list[str]:
        """Parse CORS headers from string or list."""
        if isinstance(value, str):
            return [header.strip() for header in value.split(",") if header.strip()]
        return value

    @field_validator("LOG_DIR", "UPLOAD_DIR", "YOLO_MODEL_PATH", "OCR_MODEL_PATH", mode="before")
    @classmethod
    def parse_path(cls, value: Any) -> Path:
        """Parse path from string."""
        if isinstance(value, str):
            return Path(value)
        return value

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """Build database URL from components."""
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            username=self.DATABASE_USER,
            password=self.DATABASE_PASSWORD,
            path=self.DATABASE_NAME,
        )

    @computed_field
    @property
    def SYNC_DATABASE_URL(self) -> PostgresDsn:
        """Build synchronous database URL for migrations."""
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            username=self.DATABASE_USER,
            password=self.DATABASE_PASSWORD,
            path=self.DATABASE_NAME,
        )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.YOLO_MODEL_PATH.mkdir(parents=True, exist_ok=True)
        self.OCR_MODEL_PATH.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings


# Global settings instance
settings = get_settings()
