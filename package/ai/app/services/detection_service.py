"""目标检测服务 - YOLO 封装"""
import io
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image
import cv2

from app.core.config import settings
from app.core.logger import get_logger
from app.services.model_manager import ModelManager, singleton_model_loader

logger = get_logger("detection_service")


class DetectionService:
    """目标检测服务类
    
    封装 YOLO 模型，提供目标检测功能
    """
    
    # COCO 类别名称
    COCO_NAMES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
        'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
        'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]
    
    def __init__(self):
        self.model_manager = ModelManager()
        self._model_name = f"yolo_{settings.DETECTION_MODEL}"
    
    @singleton_model_loader("yolo_{settings.DETECTION_MODEL}")
    def _load_model(self) -> Any:
        """加载 YOLO 模型"""
        try:
            # 尝试使用 ultralytics
            from ultralytics import YOLO
            
            model_path = settings.get_model_path(f"{settings.DETECTION_MODEL}.pt")
            
            # 如果本地模型不存在，自动下载
            if not model_path.exists():
                logger.info(f"Model not found locally, downloading: {settings.DETECTION_MODEL}")
                model = YOLO(settings.DETECTION_MODEL)
                # 保存到本地
                model_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                logger.info(f"Loading YOLO model from: {model_path}")
                model = YOLO(str(model_path))
            
            # 设置设备
            device = settings.actual_device
            model.to(device)
            
            logger.info(f"YOLO model loaded on device: {device}")
            return model
            
        except ImportError:
            logger.error("ultralytics not installed, detection service unavailable")
            raise RuntimeError("ultralytics is required for detection service")
    
    def _get_model(self) -> Any:
        """获取检测模型实例"""
        return self.model_manager.get_model(self._model_name)
    
    def _prepare_image(self, image_data: bytes) -> np.ndarray:
        """准备图片数据
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            numpy 数组格式的图片
        """
        # 检查图片大小
        if len(image_data) > settings.MAX_IMAGE_SIZE:
            raise ValueError(
                f"Image size exceeds limit: {len(image_data)} > {settings.MAX_IMAGE_SIZE}"
            )
        
        # 加载图片
        image = Image.open(io.BytesIO(image_data))
        
        # 转换为 RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 检查图片尺寸
        width, height = image.size
        max_dim = settings.MAX_IMAGE_DIMENSION
        if width > max_dim or height > max_dim:
            ratio = min(max_dim / width, max_dim / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Image resized from {(width, height)} to {new_size}")
        
        return np.array(image)
    
    async def detect(
        self,
        image_data: bytes,
        classes: Optional[List[int]] = None,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        return_image: bool = False
    ) -> Dict[str, Any]:
        """检测图片中的目标
        
        Args:
            image_data: 图片二进制数据
            classes: 指定检测的类别 ID 列表，None 表示检测所有类别
            conf_threshold: 置信度阈值
            iou_threshold: NMS IOU 阈值
            return_image: 是否返回带标注的图片
        
        Returns:
            检测结果字典
        """
        try:
            image = self._prepare_image(image_data)
            model = self._get_model()
            
            # 设置参数
            conf = conf_threshold or settings.DETECTION_CONF
            iou = iou_threshold or settings.DETECTION_IOU
            
            # 执行检测
            results = model(
                image,
                conf=conf,
                iou=iou,
                classes=classes,
                verbose=False
            )
            
            # 解析结果
            detections = []
            result = results[0]  # 单张图片
            
            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()
                
                for box in boxes:
                    detection = {
                        "bbox": [float(x) for x in box.xyxy[0]],  # [x1, y1, x2, y2]
                        "confidence": round(float(box.conf[0]), 4),
                        "class_id": int(box.cls[0]),
                        "class_name": self.COCO_NAMES[int(box.cls[0])]
                        if int(box.cls[0]) < len(self.COCO_NAMES) else "unknown",
                    }
                    detections.append(detection)
            
            response = {
                "success": True,
                "detection_count": len(detections),
                "detections": detections,
            }
            
            # 如果需要，返回标注图片
            if return_image and len(detections) > 0:
                annotated_image = result.plot()
                response["annotated_image"] = annotated_image.tolist()
            
            return response
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "detection_count": 0,
                "detections": [],
            }
    
    async def detect_persons(
        self,
        image_data: bytes,
        conf_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """专门检测行人
        
        Args:
            image_data: 图片二进制数据
            conf_threshold: 置信度阈值
        
        Returns:
            检测结果
        """
        result = await self.detect(
            image_data,
            classes=[0],  # person class in COCO
            conf_threshold=conf_threshold
        )
        
        if result["success"]:
            result["person_count"] = result["detection_count"]
        
        return result
    
    async def count_objects(
        self,
        image_data: bytes,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """统计图片中的目标数量
        
        Args:
            image_data: 图片二进制数据
            min_confidence: 最小置信度
        
        Returns:
            统计结果
        """
        result = await self.detect(
            image_data,
            conf_threshold=min_confidence
        )
        
        if not result["success"]:
            return result
        
        # 按类别统计
        class_counts = {}
        for det in result["detections"]:
            class_name = det["class_name"]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        return {
            "success": True,
            "total_count": result["detection_count"],
            "class_counts": class_counts,
            "detections": result["detections"],
        }
    
    async def batch_detect(
        self,
        image_data_list: List[bytes],
        conf_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """批量检测
        
        Args:
            image_data_list: 图片二进制数据列表
            conf_threshold: 置信度阈值
        
        Returns:
            检测结果列表
        """
        results = []
        for image_data in image_data_list:
            result = await self.detect(image_data, conf_threshold=conf_threshold)
            results.append(result)
        return results


# 全局目标检测服务实例
detection_service = DetectionService()
