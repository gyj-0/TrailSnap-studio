"""OCR and ticket recognition services."""

import re
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger

from .detector import DetectionBox, TicketDetector

logger = get_logger(__name__)


@dataclass
class OCRResult:
    """OCR recognition result."""

    text: str
    confidence: float
    language: str = "unknown"
    blocks: list[dict[str, Any]] | None = None

    def clean_text(self) -> str:
        """Get cleaned text (remove extra whitespace)."""
        return " ".join(self.text.split())


@dataclass
class TicketData:
    """Extracted ticket data."""

    ticket_type: str | None = None
    train_number: str | None = None
    departure_station: str | None = None
    arrival_station: str | None = None
    departure_date: date | None = None
    departure_time: time | None = None
    arrival_time: time | None = None
    seat_info: str | None = None
    price: float | None = None
    passenger_name: str | None = None
    id_number: str | None = None
    order_id: str | None = None
    raw_text: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_type": self.ticket_type,
            "train_number": self.train_number,
            "departure_station": self.departure_station,
            "arrival_station": self.arrival_station,
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
            "departure_time": self.departure_time.isoformat() if self.departure_time else None,
            "arrival_time": self.arrival_time.isoformat() if self.arrival_time else None,
            "seat_info": self.seat_info,
            "price": self.price,
            "passenger_name": self.passenger_name,
            "id_number": self.id_number,
            "order_id": self.order_id,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
        }


class OCRRecognizer:
    """
    OCR text recognition service.
    
    Note: This is a stub implementation. In production, you would
    integrate with an OCR library (Tesseract, PaddleOCR, EasyOCR, etc.).
    """

    def __init__(self, model_path: Path | str | None = None):
        """
        Initialize OCR recognizer.
        
        Args:
            model_path: Path to OCR model
        """
        self.model_path = Path(model_path or settings.OCR_MODEL_PATH)
        self._engine: Any | None = None

    async def load_engine(self) -> None:
        """Load OCR engine."""
        if self._engine is not None:
            return

        try:
            # TODO: Implement actual OCR engine loading
            # Example for Tesseract:
            # import pytesseract
            # self._engine = pytesseract
            
            # Example for PaddleOCR:
            # from paddleocr import PaddleOCR
            # self._engine = PaddleOCR(use_angle_cls=True, lang='ch')
            
            logger.info(f"OCR engine would be loaded from: {self.model_path}")
            self._engine = True  # Placeholder
        except Exception as e:
            logger.error(f"Failed to load OCR engine: {e}")
            raise

    async def recognize(
        self,
        image: Image.Image | str | Path,
        language: str = "chi_sim+eng",
    ) -> OCRResult:
        """
        Recognize text in image.
        
        Args:
            image: Input image
            language: OCR language(s)
            
        Returns:
            OCR result with recognized text
        """
        await self.load_engine()
        
        if isinstance(image, (str, Path)):
            image = Image.open(image)
        
        # TODO: Implement actual OCR
        # This is a stub that returns empty result
        
        logger.debug(f"OCR recognition would run with language: {language}")
        
        return OCRResult(
            text="",
            confidence=0.0,
            language=language,
            blocks=[],
        )

    async def recognize_region(
        self,
        image: Image.Image,
        box: DetectionBox,
    ) -> OCRResult:
        """
        Recognize text in a specific region.
        
        Args:
            image: Source image
            box: Detection box defining the region
            
        Returns:
            OCR result for the region
        """
        # Crop to region
        width, height = image.size
        x1 = int(box.x1 * width)
        y1 = int(box.y1 * height)
        x2 = int(box.x2 * width)
        y2 = int(box.y2 * height)
        
        cropped = image.crop((x1, y1, x2, y2))
        return await self.recognize(cropped)


class TicketRecognizer:
    """Railway ticket recognition service."""

    def __init__(self):
        self.detector = TicketDetector()
        self.ocr = OCRRecognizer()
        
        # Patterns for ticket field extraction
        self.patterns = {
            "train_number": re.compile(r"([GDCZTKYLS]\d{1,4})", re.IGNORECASE),
            "date": re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"),
            "time": re.compile(r"(\d{1,2}):(\d{2})"),
            "price": re.compile(r"[¥￥](\d+\.?\d*)"),
            "id_number": re.compile(r"(\d{6}\*{4,8}\d{4})"),
            "order_id": re.compile(r"([Ee]\d{9,})"),
            "seat": re.compile(r"(\d{1,2})车(\d{1,3})号"),
        }

    async def recognize_ticket(
        self,
        image: Image.Image | str | Path,
    ) -> TicketData:
        """
        Recognize and extract data from a railway ticket.
        
        Args:
            image: Input image containing ticket
            
        Returns:
            Extracted ticket data
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image)
        
        # Step 1: Detect ticket region
        detections = await self.detector.detect_tickets(image)
        
        if not detections:
            logger.warning("No ticket detected in image")
            # Try OCR on full image
            ocr_result = await self.ocr.recognize(image)
            return self._parse_ticket_text(ocr_result.text, ocr_result.confidence)
        
        # Use best detection
        best_detection = max(detections, key=lambda d: d.confidence)
        
        # Step 2: Crop ticket region
        ticket_image = await self.detector.crop_detection(image, best_detection)
        
        # Step 3: OCR on ticket region
        ocr_result = await self.ocr.recognize(ticket_image)
        
        # Step 4: Parse ticket data
        return self._parse_ticket_text(ocr_result.text, ocr_result.confidence)

    def _parse_ticket_text(self, text: str, confidence: float) -> TicketData:
        """
        Parse ticket text to extract structured data.
        
        Args:
            text: Raw OCR text
            confidence: OCR confidence
            
        Returns:
            Structured ticket data
        """
        data = TicketData(raw_text=text, confidence=confidence)
        
        # Extract train number
        train_match = self.patterns["train_number"].search(text)
        if train_match:
            data.train_number = train_match.group(1).upper()
        
        # Extract date
        date_match = self.patterns["date"].search(text)
        if date_match:
            try:
                year, month, day = map(int, date_match.groups())
                data.departure_date = date(year, month, day)
            except ValueError:
                pass
        
        # Extract times (first is departure, second is arrival)
        time_matches = self.patterns["time"].findall(text)
        if len(time_matches) >= 1:
            try:
                hour, minute = map(int, time_matches[0])
                data.departure_time = time(hour, minute)
            except ValueError:
                pass
        if len(time_matches) >= 2:
            try:
                hour, minute = map(int, time_matches[1])
                data.arrival_time = time(hour, minute)
            except ValueError:
                pass
        
        # Extract price
        price_match = self.patterns["price"].search(text)
        if price_match:
            try:
                data.price = float(price_match.group(1))
            except ValueError:
                pass
        
        # Extract seat info
        seat_match = self.patterns["seat"].search(text)
        if seat_match:
            data.seat_info = f"{seat_match.group(1)}车{seat_match.group(2)}号"
        
        # Extract ID number (masked)
        id_match = self.patterns["id_number"].search(text)
        if id_match:
            data.id_number = id_match.group(1)
        
        # Extract order ID
        order_match = self.patterns["order_id"].search(text)
        if order_match:
            data.order_id = order_match.group(1).upper()
        
        # Determine ticket type based on train number
        if data.train_number:
            train_type = data.train_number[0].upper()
            type_map = {
                "G": "高铁",
                "D": "动车",
                "C": "城际",
                "Z": "直达",
                "T": "特快",
                "K": "快速",
                "Y": "旅游",
                "L": "临客",
            }
            data.ticket_type = type_map.get(train_type, "普通")
        
        return data

    def _find_stations(self, text: str) -> tuple[str | None, str | None]:
        """
        Find departure and arrival stations in text.
        
        Args:
            text: OCR text
            
        Returns:
            Tuple of (departure_station, arrival_station)
        """
        # This is a simplified implementation
        # In production, you would use a station database or NER model
        
        # Common patterns: "XX站" -> "YY站"
        station_pattern = re.compile(r"(\S+?站)")
        stations = station_pattern.findall(text)
        
        if len(stations) >= 2:
            return stations[0], stations[1]
        elif len(stations) == 1:
            return stations[0], None
        
        return None, None


# Global recognizer instances
ocr_recognizer = OCRRecognizer()
ticket_recognizer = TicketRecognizer()
