"""EXIF data extraction utilities."""

import io
from datetime import datetime
from typing import Any

from PIL import ExifTags, Image
from PIL.ExifTags import GPSTAGS

from app.core.logger import get_logger

logger = get_logger(__name__)


class EXIFExtractor:
    """Extract and parse EXIF data from images."""

    @staticmethod
    def extract_exif(image_bytes: bytes) -> dict[str, Any]:
        """
        Extract EXIF data from image bytes.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dict with EXIF data
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            exif_data = {}

            # Get basic EXIF
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            # Get GPS info
            gps_info = {}
            if "GPSInfo" in exif_data:
                for key in exif_data["GPSInfo"].keys():
                    decode = GPSTAGS.get(key, key)
                    gps_info[decode] = exif_data["GPSInfo"][key]
                exif_data["GPSInfo"] = gps_info

            return exif_data

        except Exception as e:
            logger.error(f"Failed to extract EXIF: {e}")
            return {}

    @staticmethod
    def get_date_taken(exif_data: dict[str, Any]) -> datetime | None:
        """
        Extract date taken from EXIF data.
        
        Args:
            exif_data: EXIF data dict
            
        Returns:
            Datetime or None
        """
        date_tags = ["DateTimeOriginal", "DateTime", "DateTimeDigitized"]
        
        for tag in date_tags:
            if tag in exif_data:
                try:
                    date_str = exif_data[tag]
                    # Handle different date formats
                    if isinstance(date_str, str):
                        # Format: "2024:01:15 10:30:00"
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date from {tag}: {e}")
                    continue
        
        return None

    @staticmethod
    def get_gps_coordinates(exif_data: dict[str, Any]) -> dict[str, float | None]:
        """
        Extract GPS coordinates from EXIF data.
        
        Args:
            exif_data: EXIF data dict
            
        Returns:
            Dict with latitude, longitude, altitude
        """
        gps_info = exif_data.get("GPSInfo", {})
        
        if not gps_info:
            return {"latitude": None, "longitude": None, "altitude": None}

        def convert_to_degrees(value: tuple) -> float:
            """Convert GPS coordinates to decimal degrees."""
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = None
        lng = None
        alt = None

        try:
            # Latitude
            if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
                lat = convert_to_degrees(gps_info["GPSLatitude"])
                if gps_info["GPSLatitudeRef"] == "S":
                    lat = -lat

            # Longitude
            if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
                lng = convert_to_degrees(gps_info["GPSLongitude"])
                if gps_info["GPSLongitudeRef"] == "W":
                    lng = -lng

            # Altitude
            if "GPSAltitude" in gps_info:
                alt = float(gps_info["GPSAltitude"])
                if gps_info.get("GPSAltitudeRef") == 1:
                    alt = -alt

        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.debug(f"Failed to parse GPS coordinates: {e}")

        return {"latitude": lat, "longitude": lng, "altitude": alt}

    @staticmethod
    def get_camera_info(exif_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract camera information from EXIF.
        
        Args:
            exif_data: EXIF data dict
            
        Returns:
            Dict with camera info
        """
        return {
            "make": exif_data.get("Make"),
            "model": exif_data.get("Model"),
            "lens": exif_data.get("LensModel"),
            "software": exif_data.get("Software"),
        }

    @staticmethod
    def get_shooting_params(exif_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract shooting parameters from EXIF.
        
        Args:
            exif_data: EXIF data dict
            
        Returns:
            Dict with shooting parameters
        """
        return {
            "aperture": exif_data.get("FNumber"),
            "shutter_speed": exif_data.get("ExposureTime"),
            "iso": exif_data.get("ISOSpeedRatings"),
            "focal_length": exif_data.get("FocalLength"),
            "exposure_program": exif_data.get("ExposureProgram"),
            "metering_mode": exif_data.get("MeteringMode"),
            "flash": exif_data.get("Flash"),
            "white_balance": exif_data.get("WhiteBalance"),
        }

    @classmethod
    def extract_all(cls, image_bytes: bytes) -> dict[str, Any]:
        """
        Extract all relevant EXIF data.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dict with all extracted data
        """
        exif_data = cls.extract_exif(image_bytes)
        
        if not exif_data:
            return {}

        return {
            "raw": exif_data,
            "date_taken": cls.get_date_taken(exif_data),
            "gps": cls.get_gps_coordinates(exif_data),
            "camera": cls.get_camera_info(exif_data),
            "shooting_params": cls.get_shooting_params(exif_data),
        }


# Convenience function
async def extract_exif_data(image_bytes: bytes) -> dict[str, Any]:
    """Extract EXIF data from image bytes."""
    return EXIFExtractor.extract_all(image_bytes)
