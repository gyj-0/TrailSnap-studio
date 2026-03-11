"""File storage service for photo files."""

import hashlib
import io
import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    Service for managing file storage.
    
    Features:
    - File upload and storage
    - Thumbnail generation
    - Checksum calculation
    - File deduplication
    """

    def __init__(self):
        self.base_path = settings.UPLOAD_DIR
        self.allowed_types = settings.ALLOWED_IMAGE_TYPES
        self.max_size = settings.MAX_UPLOAD_SIZE

    def _get_user_path(self, user_id: int) -> Path:
        """Get storage path for a user."""
        return self.base_path / str(user_id)

    def _generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename."""
        ext = Path(original_filename).suffix.lower()
        return f"{uuid4().hex}{ext}"

    async def calculate_checksum(self, file_content: bytes) -> str:
        """Calculate SHA-256 checksum of file content."""
        return hashlib.sha256(file_content).hexdigest()

    async def save_file(
        self,
        user_id: int,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> dict:
        """
        Save a file to storage.
        
        Args:
            user_id: User ID
            filename: Original filename
            content: File content bytes
            mime_type: MIME type
            
        Returns:
            Dict with file info
        """
        # Validate file size
        if len(content) > self.max_size:
            raise ValueError(
                f"File size {len(content)} exceeds maximum {self.max_size}"
            )

        # Validate file type
        if mime_type not in self.allowed_types:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Calculate checksum
        checksum = await self.calculate_checksum(content)

        # Generate unique filename
        new_filename = self._generate_filename(filename)
        
        # Create user directory
        user_path = self._get_user_path(user_id)
        user_path.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = user_path / new_filename
        file_path.write_bytes(content)

        # Get image dimensions
        width, height = await self._get_image_dimensions(content)

        logger.info(f"File saved: {file_path} for user {user_id}")

        return {
            "filename": new_filename,
            "original_filename": filename,
            "file_path": str(file_path.relative_to(self.base_path)),
            "file_size": len(content),
            "mime_type": mime_type,
            "checksum": checksum,
            "width": width,
            "height": height,
        }

    async def _get_image_dimensions(self, content: bytes) -> tuple[int | None, int | None]:
        """Get image dimensions from content."""
        try:
            image = Image.open(io.BytesIO(content))
            return image.width, image.height
        except Exception:
            return None, None

    async def generate_thumbnail(
        self,
        user_id: int,
        source_path: str,
        size: tuple[int, int] = (200, 200),
        quality: int = 85,
    ) -> str:
        """
        Generate a thumbnail for an image.
        
        Args:
            user_id: User ID
            source_path: Path to source image (relative to base_path)
            size: Thumbnail size (width, height)
            quality: JPEG quality
            
        Returns:
            Path to thumbnail (relative to base_path)
        """
        source_file = self.base_path / source_path
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Create thumbnails directory
        thumbs_dir = self._get_user_path(user_id) / "thumbnails"
        thumbs_dir.mkdir(parents=True, exist_ok=True)

        # Generate thumbnail filename
        size_name = f"{size[0]}x{size[1]}"
        thumb_filename = f"{source_file.stem}_{size_name}.jpg"
        thumb_path = thumbs_dir / thumb_filename

        # Generate thumbnail
        with Image.open(source_file) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Create thumbnail
            img.thumbnail(size, Image.LANCZOS)
            img.save(thumb_path, "JPEG", quality=quality)

        return str(thumb_path.relative_to(self.base_path))

    async def generate_thumbnails(
        self,
        user_id: int,
        source_path: str,
    ) -> dict[str, str]:
        """
        Generate multiple thumbnail sizes.
        
        Args:
            user_id: User ID
            source_path: Path to source image
            
        Returns:
            Dict mapping size name to thumbnail path
        """
        sizes = {
            "small": (150, 150),
            "medium": (400, 400),
            "large": (800, 800),
        }

        thumbnails = {}
        for name, size in sizes.items():
            try:
                thumb_path = await self.generate_thumbnail(
                    user_id, source_path, size
                )
                thumbnails[name] = thumb_path
            except Exception as e:
                logger.error(f"Failed to generate {name} thumbnail: {e}")

        return thumbnails

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to file (relative to base_path)
            
        Returns:
            True if deleted, False otherwise
        """
        full_path = self.base_path / file_path
        try:
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
        return False

    async def delete_user_files(self, user_id: int) -> bool:
        """
        Delete all files for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False otherwise
        """
        user_path = self._get_user_path(user_id)
        try:
            if user_path.exists():
                shutil.rmtree(user_path)
                logger.info(f"All files deleted for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete user files for {user_id}: {e}")
        return False

    async def read_file(self, file_path: str) -> bytes:
        """
        Read file content.
        
        Args:
            file_path: Path to file (relative to base_path)
            
        Returns:
            File content as bytes
        """
        full_path = self.base_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return full_path.read_bytes()

    def get_file_url(self, file_path: str) -> str:
        """
        Get URL for a file.
        
        Args:
            file_path: Path to file (relative to base_path)
            
        Returns:
            URL string
        """
        # TODO: Implement based on your CDN/storage configuration
        return f"/uploads/{file_path}"


# Global storage service instance
storage = StorageService()
