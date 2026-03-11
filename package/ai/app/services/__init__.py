"""AI Services Module"""
from app.services.model_manager import ModelManager
from app.services.ocr_service import OCRService
from app.services.face_service import FaceService
from app.services.detection_service import DetectionService
from app.services.ticket_service import TicketService

__all__ = [
    "ModelManager",
    "OCRService", 
    "FaceService",
    "DetectionService",
    "TicketService",
]
