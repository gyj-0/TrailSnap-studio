"""YOLO-based ticket and object detector."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class DetectionType(str, Enum):
    """Types of detectable objects."""

    TICKET = "ticket"
    TRAIN = "train"
    STATION_SIGN = "station_sign"
    PLATFORM = "platform"
    QR_CODE = "qr_code"
    BARCODE = "barcode"
    TIMESTAMP = "timestamp"


@dataclass
class DetectionBox:
    """Bounding box for a detection."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name,
        }


@dataclass
class DetectionResult:
    """Result of object detection."""

    boxes: list[DetectionBox]
    image_width: int
    image_height: int
    processing_time_ms: float

    def get_by_class(self, class_name: str) -> list[DetectionBox]:
        """Get detections filtered by class name."""
        return [box for box in self.boxes if box.class_name == class_name]

    def get_best_by_class(self, class_name: str) -> DetectionBox | None:
        """Get highest confidence detection for a class."""
        boxes = self.get_by_class(class_name)
        if not boxes:
            return None
        return max(boxes, key=lambda b: b.confidence)


class TicketDetector:
    """
    YOLO-based detector for tickets and railway-related objects.
    
    Note: This is a stub implementation. In production, you would
    integrate with a real YOLO model (ultralytics, etc.).
    """

    def __init__(self, model_path: Path | str | None = None):
        """
        Initialize detector.
        
        Args:
            model_path: Path to YOLO model weights
        """
        self.model_path = Path(model_path or settings.YOLO_MODEL_PATH / "best.pt")
        self.confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD
        self._model: Any | None = None
        self._class_names: dict[int, str] = {
            0: "ticket",
            1: "train",
            2: "station_sign",
            3: "platform",
            4: "qr_code",
            5: "barcode",
            6: "timestamp",
        }

    async def load_model(self) -> None:
        """Load YOLO model."""
        if self._model is not None:
            return

        try:
            # TODO: Implement actual YOLO model loading
            # from ultralytics import YOLO
            # self._model = YOLO(str(self.model_path))
            
            logger.info(f"YOLO model would be loaded from: {self.model_path}")
            self._model = True  # Placeholder
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    async def detect(
        self,
        image: Image.Image | np.ndarray | str | Path,
        conf_threshold: float | None = None,
    ) -> DetectionResult:
        """
        Detect objects in image.
        
        Args:
            image: Input image (PIL Image, numpy array, or path)
            conf_threshold: Confidence threshold override
            
        Returns:
            Detection result with bounding boxes
        """
        import time
        
        start_time = time.time()
        
        await self.load_model()
        
        # Load image
        if isinstance(image, (str, Path)):
            image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        image_width, image_height = image.size
        
        # TODO: Implement actual detection
        # For now, return empty result
        boxes: list[DetectionBox] = []
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.debug(
            f"Detection completed in {processing_time:.2f}ms, "
            f"found {len(boxes)} objects"
        )
        
        return DetectionResult(
            boxes=boxes,
            image_width=image_width,
            image_height=image_height,
            processing_time_ms=processing_time,
        )

    async def detect_tickets(
        self,
        image: Image.Image | np.ndarray | str | Path,
    ) -> list[DetectionBox]:
        """
        Detect ticket regions in image.
        
        Args:
            image: Input image
            
        Returns:
            List of ticket detection boxes
        """
        result = await self.detect(image)
        return result.get_by_class("ticket")

    async def crop_detection(
        self,
        image: Image.Image,
        box: DetectionBox,
        padding: int = 10,
    ) -> Image.Image:
        """
        Crop image to detection box with padding.
        
        Args:
            image: Source image
            box: Detection box
            padding: Padding in pixels
            
        Returns:
            Cropped image
        """
        width, height = image.size
        
        x1 = max(0, int(box.x1 * width) - padding)
        y1 = max(0, int(box.y1 * height) - padding)
        x2 = min(width, int(box.x2 * width) + padding)
        y2 = min(height, int(box.y2 * height) + padding)
        
        return image.crop((x1, y1, x2, y2))

    def is_ticket_like(self, box: DetectionBox) -> bool:
        """
        Check if detection box has ticket-like proportions.
        
        Args:
            box: Detection box
            
        Returns:
            True if ticket-like
        """
        # Tickets typically have aspect ratio between 2:1 and 4:1
        aspect_ratio = box.width / box.height if box.height > 0 else 0
        return 1.5 <= aspect_ratio <= 5.0


# Global detector instance
detector = TicketDetector()
