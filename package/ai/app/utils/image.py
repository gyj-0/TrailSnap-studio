"""图像处理工具"""
import io
from typing import Tuple, Optional, Union
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import cv2

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("image_utils")


def validate_image(
    image_data: bytes,
    max_size: Optional[int] = None,
    allowed_formats: Optional[Tuple[str, ...]] = None
) -> Tuple[bool, str]:
    """验证图片数据
    
    Args:
        image_data: 图片二进制数据
        max_size: 最大允许大小（字节）
        allowed_formats: 允许的格式元组，如 ('JPEG', 'PNG', 'BMP')
    
    Returns:
        (是否有效, 错误信息)
    """
    max_size = max_size or settings.MAX_IMAGE_SIZE
    
    # 检查数据大小
    if len(image_data) > max_size:
        return False, f"Image size {len(image_data)} exceeds maximum {max_size}"
    
    if len(image_data) == 0:
        return False, "Empty image data"
    
    try:
        # 尝试打开图片验证格式
        with Image.open(io.BytesIO(image_data)) as img:
            # 验证格式
            if allowed_formats and img.format not in allowed_formats:
                return False, f"Unsupported format: {img.format}"
            
            # 验证图片数据完整性
            img.verify()
            
        return True, "OK"
        
    except Exception as e:
        return False, f"Invalid image: {str(e)}"


def resize_image(
    image: Union[Image.Image, np.ndarray, bytes],
    max_dimension: Optional[int] = None,
    target_size: Optional[Tuple[int, int]] = None,
    keep_aspect: bool = True,
    resample: int = Image.Resampling.LANCZOS
) -> Image.Image:
    """调整图片大小
    
    Args:
        image: 输入图片（PIL Image、numpy 数组或字节数据）
        max_dimension: 最大边长（等比例缩放）
        target_size: 目标尺寸 (width, height)
        keep_aspect: 是否保持宽高比
        resample: 重采样算法
    
    Returns:
        调整后的 PIL Image
    """
    # 统一转换为 PIL Image
    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    elif isinstance(image, np.ndarray):
        if image.shape[2] == 3:
            img = Image.fromarray(image)
        else:
            img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        img = image.copy()
    
    original_size = img.size
    
    if target_size:
        # 调整到目标尺寸
        if keep_aspect:
            img.thumbnail(target_size, resample)
        else:
            img = img.resize(target_size, resample)
    elif max_dimension:
        # 按最大边等比例缩放
        max_dim = max_dimension or settings.MAX_IMAGE_DIMENSION
        width, height = img.size
        
        if width > max_dim or height > max_dim:
            ratio = min(max_dim / width, max_dim / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, resample)
            logger.debug(f"Image resized from {original_size} to {new_size}")
    
    return img


def convert_to_rgb(
    image: Union[Image.Image, np.ndarray, bytes],
    force_copy: bool = False
) -> Image.Image:
    """转换图片为 RGB 格式
    
    Args:
        image: 输入图片
        force_copy: 是否强制复制
    
    Returns:
        RGB 格式的 PIL Image
    """
    # 统一转换为 PIL Image
    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    elif isinstance(image, np.ndarray):
        # 假设 OpenCV 格式 BGR
        if len(image.shape) == 3:
            img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            img = Image.fromarray(image)
    else:
        img = image if force_copy else image.copy()
    
    # 转换模式
    if img.mode in ('RGBA', 'LA', 'P'):
        # 透明通道转为白色背景
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode in ('RGBA', 'LA'):
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    return img


def get_image_info(image_data: bytes) -> dict:
    """获取图片信息
    
    Args:
        image_data: 图片二进制数据
    
    Returns:
        图片信息字典
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            return {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "size_bytes": len(image_data),
                "aspect_ratio": round(img.width / img.height, 4) if img.height > 0 else 0,
            }
    except Exception as e:
        return {
            "error": str(e),
            "size_bytes": len(image_data),
        }


def preprocess_for_model(
    image_data: bytes,
    target_size: Optional[Tuple[int, int]] = None,
    normalize: bool = True,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
    to_tensor: bool = True
) -> np.ndarray:
    """预处理图片用于深度学习模型
    
    Args:
        image_data: 图片二进制数据
        target_size: 目标尺寸 (H, W)
        normalize: 是否归一化
        mean: 均值（用于归一化）
        std: 标准差（用于归一化）
        to_tensor: 是否转换为 CHW 格式
    
    Returns:
        预处理后的 numpy 数组
    """
    # 加载并转换为 RGB
    img = convert_to_rgb(image_data)
    
    # 调整大小
    if target_size:
        img = img.resize((target_size[1], target_size[0]), Image.Resampling.LANCZOS)
    
    # 转换为 numpy 数组 [H, W, C]
    img_array = np.array(img).astype(np.float32)
    
    # 归一化到 [0, 1]
    img_array = img_array / 255.0
    
    # ImageNet 标准化
    if normalize:
        img_array = (img_array - np.array(mean)) / np.array(std)
    
    # 转换为 CHW 格式
    if to_tensor:
        img_array = np.transpose(img_array, (2, 0, 1))
    
    return img_array


def enhance_image(
    image: Union[Image.Image, np.ndarray, bytes],
    brightness: float = 1.0,
    contrast: float = 1.0,
    sharpness: float = 1.0
) -> Image.Image:
    """增强图片质量
    
    Args:
        image: 输入图片
        brightness: 亮度因子
        contrast: 对比度因子
        sharpness: 锐度因子
    
    Returns:
        增强后的图片
    """
    from PIL import ImageEnhance
    
    # 转换为 PIL Image
    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    elif isinstance(image, np.ndarray):
        img = Image.fromarray(image)
    else:
        img = image.copy()
    
    # 应用增强
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
    
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)
    
    return img


def auto_rotate(image_data: bytes) -> Image.Image:
    """根据 EXIF 信息自动旋转图片
    
    Args:
        image_data: 图片二进制数据
    
    Returns:
        正确方向的图片
    """
    img = Image.open(io.BytesIO(image_data))
    
    try:
        # 根据 EXIF 信息旋转
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    
    return img


def create_thumbnail(
    image_data: bytes,
    size: Tuple[int, int] = (128, 128),
    format: str = "JPEG",
    quality: int = 85
) -> bytes:
    """创建缩略图
    
    Args:
        image_data: 原始图片数据
        size: 缩略图尺寸
        format: 输出格式
        quality: JPEG 质量
    
    Returns:
        缩略图二进制数据
    """
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format=format, quality=quality)
    return output.getvalue()


def crop_image(
    image: Union[Image.Image, bytes],
    bbox: Tuple[float, float, float, float],
    relative: bool = False
) -> Image.Image:
    """裁剪图片
    
    Args:
        image: 输入图片
        bbox: 裁剪框 (x1, y1, x2, y2)
        relative: 是否为相对坐标 (0-1)
    
    Returns:
        裁剪后的图片
    """
    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    else:
        img = image.copy()
    
    width, height = img.size
    
    if relative:
        x1, y1, x2, y2 = bbox
        bbox = (
            int(x1 * width),
            int(y1 * height),
            int(x2 * width),
            int(y2 * height)
        )
    
    return img.crop(bbox)


def draw_boxes(
    image: Union[Image.Image, np.ndarray, bytes],
    boxes: list,
    labels: Optional[list] = None,
    colors: Optional[list] = None,
    thickness: int = 2
) -> np.ndarray:
    """在图片上绘制检测框
    
    Args:
        image: 输入图片
        boxes: 框坐标列表 [[x1, y1, x2, y2], ...]
        labels: 标签列表
        colors: 颜色列表 [(B, G, R), ...]
        thickness: 线宽
    
    Returns:
        绘制后的 numpy 数组 (BGR 格式)
    """
    # 转换为 OpenCV 格式
    if isinstance(image, bytes):
        img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    elif isinstance(image, Image.Image):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        img = image.copy()
    
    default_colors = [
        (0, 255, 0),    # 绿
        (255, 0, 0),    # 蓝
        (0, 0, 255),    # 红
        (255, 255, 0),  # 青
        (255, 0, 255),  # 紫
        (0, 255, 255),  # 黄
    ]
    
    for i, box in enumerate(boxes):
        color = colors[i] if colors and i < len(colors) else default_colors[i % len(default_colors)]
        x1, y1, x2, y2 = map(int, box)
        
        # 绘制矩形
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        
        # 绘制标签
        if labels and i < len(labels):
            label = str(labels[i])
            (text_width, text_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                img,
                (x1, y1 - text_height - 4),
                (x1 + text_width, y1),
                color,
                -1
            )
            cv2.putText(
                img,
                label,
                (x1, y1 - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
    
    return img
