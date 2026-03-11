"""AI Service Routers Module"""
from fastapi import APIRouter

from app.routers import ocr, face, detection, tickets


def create_api_router() -> APIRouter:
    """创建并配置 API 路由器"""
    api_router = APIRouter(prefix="/api/v1")
    
    # 注册各功能路由
    api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
    api_router.include_router(face.router, prefix="/face", tags=["Face Recognition"])
    api_router.include_router(detection.router, prefix="/detection", tags=["Object Detection"])
    api_router.include_router(tickets.router, prefix="/tickets", tags=["Ticket Recognition"])
    
    return api_router
