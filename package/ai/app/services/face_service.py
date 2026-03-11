"""人脸识别服务 - InsightFace 封装"""
import io
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2

from app.core.config import settings
from app.core.logger import get_logger
from app.services.model_manager import ModelManager, singleton_model_loader

logger = get_logger("face_service")


class FaceService:
    """人脸识别服务类
    
    封装 InsightFace，提供人脸检测、特征提取和比对功能
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
        self._det_model_name = "face_detection"
        self._rec_model_name = "face_recognition"
        self._face_db: Dict[str, np.ndarray] = {}  # 简单的人脸特征库
    
    @singleton_model_loader("face_detection")
    def _load_detection_model(self) -> Any:
        """加载人脸检测模型"""
        import insightface
        from insightface.app import FaceAnalysis
        
        logger.info(f"Loading FaceAnalysis model: {settings.FACE_MODEL_NAME}")
        
        app = FaceAnalysis(
            name=settings.FACE_MODEL_NAME,
            root=str(settings.MODELS_DIR),
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            if settings.is_gpu_available else ['CPUExecutionProvider']
        )
        app.prepare(ctx_id=settings.GPU_ID if settings.is_gpu_available else -1, det_size=(640, 640))
        
        return app
    
    def _get_model(self) -> Any:
        """获取人脸分析模型实例"""
        return self.model_manager.get_model(self._det_model_name)
    
    def _prepare_image(self, image_data: bytes) -> np.ndarray:
        """准备图片数据
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            OpenCV 格式的图片 (BGR)
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
        
        # 转换为 OpenCV 格式 (BGR)
        img_array = np.array(image)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_cv
    
    async def detect(
        self,
        image_data: bytes,
        return_landmarks: bool = False,
        return_attributes: bool = False
    ) -> Dict[str, Any]:
        """检测图片中的人脸
        
        Args:
            image_data: 图片二进制数据
            return_landmarks: 是否返回关键点
            return_attributes: 是否返回属性（年龄、性别等）
        
        Returns:
            检测结果字典
        """
        try:
            image = self._prepare_image(image_data)
            model = self._get_model()
            
            # 执行人脸检测
            faces = model.get(image)
            
            face_list = []
            for face in faces:
                face_info = {
                    "face_id": id(face),
                    "bbox": [float(x) for x in face.bbox],  # [x1, y1, x2, y2]
                    "det_score": round(float(face.det_score), 4),
                }
                
                if return_landmarks and hasattr(face, 'kps'):
                    face_info["landmarks"] = face.kps.tolist()
                
                if return_attributes:
                    if hasattr(face, 'age') and face.age is not None:
                        face_info["age"] = int(face.age)
                    if hasattr(face, 'gender') and face.gender is not None:
                        face_info["gender"] = "male" if face.gender == 1 else "female"
                    if hasattr(face, 'embedding') and face.embedding is not None:
                        face_info["has_embedding"] = True
                
                face_list.append(face_info)
            
            return {
                "success": True,
                "face_count": len(face_list),
                "faces": face_list,
            }
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "face_count": 0,
                "faces": [],
            }
    
    async def extract_embedding(
        self,
        image_data: bytes
    ) -> Dict[str, Any]:
        """提取人脸特征向量
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            特征向量结果
        """
        try:
            image = self._prepare_image(image_data)
            model = self._get_model()
            
            faces = model.get(image)
            
            if not faces:
                return {
                    "success": False,
                    "error": "No face detected",
                    "embedding": None,
                }
            
            # 取最大人脸
            face = max(faces, key=lambda f: f.det_score)
            
            if face.det_score < settings.FACE_DET_THRESHOLD:
                return {
                    "success": False,
                    "error": f"Face detection score too low: {face.det_score:.4f}",
                    "embedding": None,
                }
            
            embedding = face.embedding.tolist()
            
            return {
                "success": True,
                "embedding": embedding,
                "embedding_size": len(embedding),
                "det_score": round(float(face.det_score), 4),
                "bbox": [float(x) for x in face.bbox],
            }
            
        except Exception as e:
            logger.error(f"Face embedding extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "embedding": None,
            }
    
    async def compare(
        self,
        image1_data: bytes,
        image2_data: bytes
    ) -> Dict[str, Any]:
        """比对两张人脸图片
        
        Args:
            image1_data: 第一张图片二进制数据
            image2_data: 第二张图片二进制数据
        
        Returns:
            比对结果
        """
        try:
            # 提取两张图片的特征
            result1 = await self.extract_embedding(image1_data)
            result2 = await self.extract_embedding(image2_data)
            
            if not result1["success"]:
                return {
                    "success": False,
                    "error": f"Image 1: {result1.get('error', 'Unknown error')}",
                    "similarity": 0.0,
                    "is_same_person": False,
                }
            
            if not result2["success"]:
                return {
                    "success": False,
                    "error": f"Image 2: {result2.get('error', 'Unknown error')}",
                    "similarity": 0.0,
                    "is_same_person": False,
                }
            
            # 计算余弦相似度
            embedding1 = np.array(result1["embedding"])
            embedding2 = np.array(result2["embedding"])
            
            similarity = self._cosine_similarity(embedding1, embedding2)
            is_same = similarity >= settings.FACE_RECOGNITION_THRESHOLD
            
            return {
                "success": True,
                "similarity": round(float(similarity), 4),
                "is_same_person": bool(is_same),
                "threshold": settings.FACE_RECOGNITION_THRESHOLD,
            }
            
        except Exception as e:
            logger.error(f"Face comparison failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "similarity": 0.0,
                "is_same_person": False,
            }
    
    async def search(
        self,
        image_data: bytes,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """在人脸库中搜索
        
        Args:
            image_data: 查询图片二进制数据
            top_k: 返回最相似的 top_k 个结果
        
        Returns:
            搜索结果
        """
        try:
            # 提取查询人脸特征
            result = await self.extract_embedding(image_data)
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to extract embedding"),
                    "results": [],
                }
            
            if not self._face_db:
                return {
                    "success": True,
                    "warning": "Face database is empty",
                    "results": [],
                }
            
            query_embedding = np.array(result["embedding"])
            
            # 计算与库中所有人脸的相似度
            similarities = []
            for face_id, db_embedding in self._face_db.items():
                sim = self._cosine_similarity(query_embedding, db_embedding)
                similarities.append({
                    "face_id": face_id,
                    "similarity": round(float(sim), 4),
                })
            
            # 排序并返回 top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return {
                "success": True,
                "query_face": {
                    "det_score": result["det_score"],
                    "bbox": result["bbox"],
                },
                "results": similarities[:top_k],
            }
            
        except Exception as e:
            logger.error(f"Face search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }
    
    def register_face(
        self,
        face_id: str,
        embedding: List[float]
    ) -> Dict[str, Any]:
        """注册人脸到数据库（同步方法，通常由上层调用）
        
        Args:
            face_id: 人脸标识
            embedding: 人脸特征向量
        
        Returns:
            注册结果
        """
        try:
            self._face_db[face_id] = np.array(embedding)
            return {
                "success": True,
                "face_id": face_id,
                "database_size": len(self._face_db),
            }
        except Exception as e:
            logger.error(f"Face registration failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def remove_face(self, face_id: str) -> Dict[str, Any]:
        """从数据库移除人脸
        
        Args:
            face_id: 人脸标识
        
        Returns:
            移除结果
        """
        if face_id in self._face_db:
            del self._face_db[face_id]
            return {
                "success": True,
                "message": f"Face '{face_id}' removed",
                "database_size": len(self._face_db),
            }
        return {
            "success": False,
            "error": f"Face '{face_id}' not found",
        }
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度
        
        Args:
            a: 向量 a
            b: 向量 b
        
        Returns:
            余弦相似度 [-1, 1]
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))


# 全局人脸识别服务实例
face_service = FaceService()
