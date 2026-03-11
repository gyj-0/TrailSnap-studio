"""OCR 路由"""
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field

from app.services.ocr_service import ocr_service
from app.core.logger import get_logger

logger = get_logger("ocr_router")
router = APIRouter()


class OCRResponse(BaseModel):
    """OCR 响应模型"""
    success: bool = Field(..., description="是否成功")
    text_count: int = Field(0, description="识别文本数量")
    avg_confidence: float = Field(0.0, description="平均置信度")
    results: list = Field(default_factory=list, description="识别结果列表")
    error: Optional[str] = Field(None, description="错误信息")


class OCRDetectResponse(BaseModel):
    """OCR 检测响应模型"""
    success: bool = Field(..., description="是否成功")
    box_count: int = Field(0, description="检测框数量")
    boxes: list = Field(default_factory=list, description="文本框坐标列表")
    error: Optional[str] = Field(None, description="错误信息")


class OCRStructureResponse(BaseModel):
    """OCR 结构化响应模型"""
    success: bool = Field(..., description="是否成功")
    text_count: int = Field(0, description="文本数量")
    lines: list = Field(default_factory=list, description="按行组织的文本")
    full_text: str = Field("", description="完整文本")
    error: Optional[str] = Field(None, description="错误信息")


@router.post("/recognize", response_model=OCRResponse)
async def recognize_text(
    file: UploadFile = File(..., description="待识别的图片文件"),
    return_boxes: bool = Form(True, description="是否返回文本框坐标"),
    return_confidence: bool = Form(True, description="是否返回置信度"),
):
    """识别图片中的文本
    
    支持 JPG、PNG、BMP 等常见图片格式
    """
    logger.info(f"OCR recognize request: file={file.filename}, "
                f"return_boxes={return_boxes}, return_confidence={return_confidence}")
    
    # 验证文件类型
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {allowed_types}"
        )
    
    try:
        image_data = await file.read()
        result = await ocr_service.recognize(
            image_data,
            return_boxes=return_boxes,
            return_confidence=return_confidence
        )
        return OCRResponse(**result)
    except Exception as e:
        logger.error(f"OCR recognize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect", response_model=OCRDetectResponse)
async def detect_text_regions(
    file: UploadFile = File(..., description="待检测的图片文件"),
):
    """仅检测图片中的文本区域（不识别内容）
    
    返回文本框的位置坐标
    """
    logger.info(f"OCR detect request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await ocr_service.detect(image_data)
        return OCRDetectResponse(**result)
    except Exception as e:
        logger.error(f"OCR detect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/structure", response_model=OCRStructureResponse)
async def recognize_structure(
    file: UploadFile = File(..., description="待识别的图片文件"),
):
    """结构化文档识别
    
    按行组织文本，适合文档、表格等结构化内容的识别
    """
    logger.info(f"OCR structure request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await ocr_service.recognize_structure(image_data)
        return OCRStructureResponse(**result)
    except Exception as e:
        logger.error(f"OCR structure error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
