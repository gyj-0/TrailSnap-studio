"""Filename utilities for safe and consistent file naming."""

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Characters not allowed in filenames
INVALID_CHARS = re.compile(r'[<>:\"/\\|?*\x00-\x1f]')

# Reserved Windows filenames
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
    "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
    "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Maximum filename length (conservative for cross-platform)
MAX_FILENAME_LENGTH = 200


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize a filename to be safe for all filesystems.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    # Normalize unicode characters
    filename = unicodedata.normalize("NFKC", filename)
    
    # Remove invalid characters
    filename = INVALID_CHARS.sub("_", filename)
    
    # Remove control characters
    filename = "".join(char for char in filename if ord(char) >= 32)
    
    # Strip whitespace and dots from ends
    filename = filename.strip(" .")
    
    # Check for reserved names (Windows)
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in RESERVED_NAMES:
        filename = f"_{filename}"
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    # Truncate if too long (preserve extension)
    if len(filename) > max_length:
        path = Path(filename)
        stem = path.stem
        suffix = path.suffix
        max_stem_length = max_length - len(suffix)
        if max_stem_length < 1:
            # Extension itself is too long, just truncate everything
            filename = filename[:max_length]
        else:
            filename = stem[:max_stem_length] + suffix
    
    return filename


def generate_unique_filename(
    original_filename: str,
    prefix: str | None = None,
    suffix: str | None = None,
    timestamp: bool = False,
    use_uuid: bool = False,
) -> str:
    """
    Generate a unique filename with optional prefix/suffix/timestamp.
    
    Args:
        original_filename: Original filename
        prefix: Optional prefix to add
        suffix: Optional suffix to add (before extension)
        timestamp: Whether to add timestamp
        use_uuid: Whether to use UUID as filename
        
    Returns:
        Generated filename
    """
    path = Path(original_filename)
    ext = path.suffix.lower()
    
    if use_uuid:
        stem = uuid4().hex
    else:
        stem = path.stem
    
    parts = []
    
    if prefix:
        parts.append(prefix)
    
    if timestamp:
        parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    parts.append(stem)
    
    if suffix:
        parts.append(suffix)
    
    new_stem = "_".join(parts)
    return sanitize_filename(f"{new_stem}{ext}")


def get_safe_extension(filename: str) -> str:
    """
    Get the file extension in lowercase.
    
    Args:
        filename: Filename
        
    Returns:
        Lowercase extension including the dot
    """
    return Path(filename).suffix.lower()


def is_valid_image_extension(filename: str, allowed_extensions: set[str] | None = None) -> bool:
    """
    Check if filename has a valid image extension.
    
    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (defaults to common image types)
        
    Returns:
        True if valid image extension
    """
    if allowed_extensions is None:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".raw"}
    
    ext = get_safe_extension(filename)
    return ext in allowed_extensions


def generate_date_based_path(
    base_dir: str | Path,
    date: datetime | None = None,
    filename: str | None = None,
) -> Path:
    """
    Generate a date-based directory path.
    
    Args:
        base_dir: Base directory
        date: Date to use (defaults to now)
        filename: Optional filename to append
        
    Returns:
        Path object
    """
    if date is None:
        date = datetime.now()
    
    path = Path(base_dir) / str(date.year) / f"{date.month:02d}"
    
    if filename:
        path = path / sanitize_filename(filename)
    
    return path


def truncate_filename(
    filename: str,
    max_length: int = MAX_FILENAME_LENGTH,
    placeholder: str = "...",
) -> str:
    """
    Truncate filename while preserving extension.
    
    Args:
        filename: Original filename
        max_length: Maximum length
        placeholder: Placeholder for truncated part
        
    Returns:
        Truncated filename
    """
    if len(filename) <= max_length:
        return filename
    
    path = Path(filename)
    ext = path.suffix
    stem = path.stem
    
    # Calculate available space for stem
    available = max_length - len(ext) - len(placeholder)
    
    if available < 1:
        # Can't fit even with truncation
        return filename[:max_length]
    
    return f"{stem[:available]}{placeholder}{ext}"


def clean_path_for_display(path: str | Path) -> str:
    """
    Clean a path for display purposes.
    
    Args:
        path: Path to clean
        
    Returns:
        Cleaned path string
    """
    return str(path).replace("\\", "/")
