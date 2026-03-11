"""人脸识别路由"""
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field

from app.services.face_service import face_service
from app.core.logger import get_logger

logger = get_logger("face_router")
router = APIRouter()


class FaceDetectResponse(BaseModel):
    """人脸检测响应模型"""
    success: bool = Field(..., description="是否成功")
    face_count: int = Field(0, description="检测到的人脸数量")
    faces: list = Field(default_factory=list, description="人脸信息列表")
    error: Optional[str] = Field(None, description="错误信息")


class FaceEmbeddingResponse(BaseModel):
    """人脸特征提取响应模型"""
    success: bool = Field(..., description="是否成功")
    embedding: Optional[List[float]] = Field(None, description="特征向量")
    embedding_size: int = Field(0, description="特征向量维度")
    det_score: float = Field(0.0, description="检测置信度")
    bbox: Optional[List[float]] = Field(None, description="人脸框坐标 [x1, y1, x2, y2]")
    error: Optional[str] = Field(None, description="错误信息")


class FaceCompareResponse(BaseModel):
    """人脸比对响应模型"""
    success: bool = Field(..., description="是否成功")
    similarity: float = Field(0.0, description="相似度 (0-1)", ge=0, le=1)
    is_same_person: bool = Field(False, description="是否为同一人")
    threshold: float = Field(0.6, description="判定阈值")
    error: Optional[str] = Field(None, description="错误信息")


class FaceSearchResponse(BaseModel):
    """人脸搜索响应模型"""
    success: bool = Field(..., description="是否成功")
    query_face: Optional[dict] = Field(None, description="查询人脸信息")
    results: list = Field(default_factory=list, description="搜索结果列表")
    error: Optional[str] = Field(None, description="错误信息")


@router.post("/detect", response_model=FaceDetectResponse)
async def detect_faces(
    file: UploadFile = File(..., description="待检测的图片文件"),
    return_landmarks: bool = Form(False, description="是否返回人脸关键点"),
    return_attributes: bool = Form(False, description="是否返回人脸属性（年龄、性别等）"),
):
    """检测图片中的人脸
    
    返回人脸位置、检测置信度等信息
    """
    logger.info(f"Face detect request: file={file.filename}, "
                f"landmarks={return_landmarks}, attributes={return_attributes}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await face_service.detect(
            image_data,
            return_landmarks=return_landmarks,
            return_attributes=return_attributes
        )
        return FaceDetectResponse(**result)
    except Exception as e:
        logger.error(f"Face detect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embedding", response_model=FaceEmbeddingResponse)
async def extract_face_embedding(
    file: UploadFile = File(..., description="包含人脸的图片文件"),
):
    """提取人脸特征向量
    
    返回可用于人脸比对的高维特征向量
    """
    logger.info(f"Face embedding request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await face_service.extract_embedding(image_data)
        return FaceEmbeddingResponse(**result)
    except Exception as e:
        logger.error(f"Face embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=FaceCompareResponse)
async def compare_faces(
    file1: UploadFile = File(..., description="第一张人脸图片"),
    file2: UploadFile = File(..., description="第二张人脸图片"),
):
    """比对两张人脸图片
    
    判断是否为同一人，返回相似度分数
    """
    logger.info(f"Face compare request: file1={file1.filename}, file2={file2.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    for file in [file1, file2]:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type for {file.filename}: {file.content_type}"
            )
    
    try:
        image1_data = await file1.read()
        image2_data = await file2.read()
        result = await face_service.compare(image1_data, image2_data)
        return FaceCompareResponse(**result)
    except Exception as e:
        logger.error(f"Face compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=FaceSearchResponse)
async def search_face(
    file: UploadFile = File(..., description="待搜索的人脸图片"),
    top_k: int = Form(5, ge=1, le=20, description="返回最相似的 top_k 个结果"),
):
    """在人脸库中搜索相似人脸
    
    需要在服务中先注册人脸
    """
    logger.info(f"Face search request: file={file.filename}, top_k={top_k}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await face_service.search(image_data, top_k=top_k)
        return FaceSearchResponse(**result)
    except Exception as e:
        logger.error(f"Face search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/{face_id}")
async def register_face(
    face_id: str,
    file: UploadFile = File(..., description="要注册的人脸图片"),
):
    """注册人脸到人脸库
    
    - **face_id**: 人脸的唯一标识
    - **file**: 包含清晰人脸的图片
    """
    logger.info(f"Face register request: face_id={face_id}, file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        
        # 先提取特征
        result = await face_service.extract_embedding(image_data)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to extract embedding"))
        
        # 注册人脸
        register_result = face_service.register_face(face_id, result["embedding"])
        return register_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face register error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/register/{face_id}")
async def remove_registered_face(face_id: str):
    """从人脸库中移除已注册的人脸"""
    logger.info(f"Face remove request: face_id={face_id}")
    
    result = face_service.remove_face(face_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Face not found"))
    
    return result
