"""目标检测路由"""
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.detection_service import detection_service
from app.core.logger import get_logger

logger = get_logger("detection_router")
router = APIRouter()


class DetectionResponse(BaseModel):
    """目标检测响应模型"""
    success: bool = Field(..., description="是否成功")
    detection_count: int = Field(0, description="检测到的目标数量")
    detections: list = Field(default_factory=list, description="检测结果列表")
    error: Optional[str] = Field(None, description="错误信息")


class DetectionItem(BaseModel):
    """检测项目"""
    bbox: List[float] = Field(..., description="边界框坐标 [x1, y1, x2, y2]")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    class_id: int = Field(..., description="类别 ID")
    class_name: str = Field(..., description="类别名称")


class PersonDetectionResponse(BaseModel):
    """行人检测响应模型"""
    success: bool = Field(..., description="是否成功")
    person_count: int = Field(0, description="检测到的行人数量")
    detections: List[DetectionItem] = Field(default_factory=list, description="检测结果")
    error: Optional[str] = Field(None, description="错误信息")


class CountResponse(BaseModel):
    """统计响应模型"""
    success: bool = Field(..., description="是否成功")
    total_count: int = Field(0, description="总数量")
    class_counts: dict = Field(default_factory=dict, description="按类别统计")
    error: Optional[str] = Field(None, description="错误信息")


@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    file: UploadFile = File(..., description="待检测的图片文件"),
    classes: Optional[str] = Form(None, description="指定检测的类别 ID，逗号分隔，如 '0,2,3'"),
    conf_threshold: Optional[float] = Form(None, ge=0, le=1, description="置信度阈值"),
    iou_threshold: Optional[float] = Form(None, ge=0, le=1, description="NMS IOU 阈值"),
):
    """检测图片中的目标
    
    支持 COCO 数据集的 80 个类别，包括：
    - person (0): 行人
    - car (2): 汽车
    - bicycle (1): 自行车
    - etc.
    
    完整类别列表见响应中的 class_name
    """
    logger.info(f"Object detection request: file={file.filename}, classes={classes}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        # 解析类别列表
        class_list = None
        if classes:
            try:
                class_list = [int(c.strip()) for c in classes.split(",")]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid classes format, expected comma-separated integers")
        
        image_data = await file.read()
        result = await detection_service.detect(
            image_data,
            classes=class_list,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )
        return DetectionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Object detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/persons", response_model=PersonDetectionResponse)
async def detect_persons(
    file: UploadFile = File(..., description="待检测的图片文件"),
    conf_threshold: Optional[float] = Form(None, ge=0, le=1, description="置信度阈值"),
):
    """专门检测图片中的行人
    
    只返回 person 类别的检测结果
    """
    logger.info(f"Person detection request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await detection_service.detect_persons(
            image_data,
            conf_threshold=conf_threshold
        )
        return PersonDetectionResponse(**result)
    except Exception as e:
        logger.error(f"Person detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/count", response_model=CountResponse)
async def count_objects(
    file: UploadFile = File(..., description="待检测的图片文件"),
    min_confidence: float = Form(0.5, ge=0, le=1, description="最小置信度"),
):
    """统计图片中的目标数量
    
    按类别统计检测到的目标数量
    """
    logger.info(f"Object count request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await detection_service.count_objects(
            image_data,
            min_confidence=min_confidence
        )
        return CountResponse(**result)
    except Exception as e:
        logger.error(f"Object count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes")
async def get_classes():
    """获取支持的检测类别列表"""
    from app.services.detection_service import DetectionService
    
    classes = [
        {"id": i, "name": name}
        for i, name in enumerate(DetectionService.COCO_NAMES)
    ]
    
    return {
        "total": len(classes),
        "classes": classes
    }
