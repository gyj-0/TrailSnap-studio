"""OCR 服务 - PaddleOCR 封装"""
import io
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger
from app.services.model_manager import ModelManager, singleton_model_loader

logger = get_logger("ocr_service")


class OCRService:
    """OCR 服务类
    
    封装 PaddleOCR，提供文本检测和识别功能
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
        self._model_name = "paddle_ocr"
    
    @singleton_model_loader("paddle_ocr")
    def _load_model(self) -> Any:
        """加载 PaddleOCR 模型"""
        from paddleocr import PaddleOCR
        
        use_gpu = settings.OCR_USE_GPU and settings.is_gpu_available
        
        logger.info(f"Loading PaddleOCR (use_gpu={use_gpu})")
        
        ocr = PaddleOCR(
            use_angle_cls=settings.OCR_USE_ANGLE_CLS,
            lang=settings.OCR_LANG,
            use_gpu=use_gpu,
            gpu_id=settings.GPU_ID if use_gpu else 0,
            show_log=False,
        )
        return ocr
    
    def _get_model(self) -> Any:
        """获取 OCR 模型实例"""
        return self.model_manager.get_model(self._model_name)
    
    async def recognize(
        self,
        image_data: bytes,
        return_boxes: bool = True,
        return_confidence: bool = True
    ) -> Dict[str, Any]:
        """识别图片中的文本
        
        Args:
            image_data: 图片二进制数据
            return_boxes: 是否返回文本框坐标
            return_confidence: 是否返回置信度
        
        Returns:
            识别结果字典
        """
        try:
            # 验证并处理图片
            image = self._prepare_image(image_data)
            
            # 获取模型并执行识别
            model = self._get_model()
            result = model.ocr(image, cls=True)
            
            # 解析结果
            text_results = []
            total_confidence = 0.0
            count = 0
            
            if result and result[0]:
                for line in result[0]:
                    if line:
                        box = line[0]  # 文本框坐标
                        text = line[1][0]  # 文本内容
                        confidence = line[1][1]  # 置信度
                        
                        item = {"text": text}
                        if return_boxes:
                            item["box"] = box
                        if return_confidence:
                            item["confidence"] = round(float(confidence), 4)
                        
                        text_results.append(item)
                        total_confidence += confidence
                        count += 1
            
            avg_confidence = total_confidence / count if count > 0 else 0.0
            
            return {
                "success": True,
                "text_count": len(text_results),
                "avg_confidence": round(avg_confidence, 4),
                "results": text_results,
            }
            
        except Exception as e:
            logger.error(f"OCR recognition failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text_count": 0,
                "avg_confidence": 0.0,
                "results": [],
            }
    
    async def detect(
        self,
        image_data: bytes
    ) -> Dict[str, Any]:
        """仅检测文本区域（不识别）
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            检测结果字典
        """
        try:
            image = self._prepare_image(image_data)
            model = self._get_model()
            
            # 仅执行检测
            result = model.ocr(image, det=True, rec=False, cls=False)
            
            boxes = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        boxes.append(line)
            
            return {
                "success": True,
                "box_count": len(boxes),
                "boxes": boxes,
            }
            
        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "box_count": 0,
                "boxes": [],
            }
    
    async def recognize_structure(
        self,
        image_data: bytes
    ) -> Dict[str, Any]:
        """结构化文档识别（表格、版面分析）
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            结构化识别结果
        """
        try:
            image = self._prepare_image(image_data)
            model = self._get_model()
            
            # 执行版面分析
            result = model.ocr(image, cls=True)
            
            # 按垂直位置排序文本，构建结构化输出
            text_blocks = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        box = line[0]
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        # 计算中心点 Y 坐标用于排序
                        center_y = sum(point[1] for point in box) / 4
                        
                        text_blocks.append({
                            "text": text,
                            "box": box,
                            "confidence": round(float(confidence), 4),
                            "center_y": center_y,
                        })
            
            # 按垂直位置排序
            text_blocks.sort(key=lambda x: x["center_y"])
            
            # 按行分组
            lines = self._group_by_lines(text_blocks)
            
            return {
                "success": True,
                "text_count": len(text_blocks),
                "lines": lines,
                "full_text": "\n".join(lines),
            }
            
        except Exception as e:
            logger.error(f"OCR structure recognition failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text_count": 0,
                "lines": [],
                "full_text": "",
            }
    
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
        
        # 转换为 RGB（去除透明通道）
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # 检查图片尺寸
        width, height = image.size
        max_dim = settings.MAX_IMAGE_DIMENSION
        if width > max_dim or height > max_dim:
            # 等比例缩放
            ratio = min(max_dim / width, max_dim / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Image resized from {(width, height)} to {new_size}")
        
        return np.array(image)
    
    def _group_by_lines(
        self,
        text_blocks: List[Dict[str, Any]],
        y_threshold: float = 10.0
    ) -> List[str]:
        """将文本块按行分组
        
        Args:
            text_blocks: 文本块列表
            y_threshold: Y 轴阈值
        
        Returns:
            按行组织的文本列表
        """
        if not text_blocks:
            return []
        
        lines = []
        current_line = [text_blocks[0]]
        current_y = text_blocks[0]["center_y"]
        
        for block in text_blocks[1:]:
            if abs(block["center_y"] - current_y) <= y_threshold:
                current_line.append(block)
            else:
                # 按 X 坐标排序当前行
                current_line.sort(key=lambda x: x["box"][0][0])
                lines.append(" ".join(b["text"] for b in current_line))
                
                current_line = [block]
                current_y = block["center_y"]
        
        # 处理最后一行
        if current_line:
            current_line.sort(key=lambda x: x["box"][0][0])
            lines.append(" ".join(b["text"] for b in current_line))
        
        return lines


# 全局 OCR 服务实例
ocr_service = OCRService()
