"""
视频生成API客户端基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class VideoGenerationRequest:
    """视频生成请求"""
    def __init__(
        self,
        prompt: str,
        duration: float,
        resolution: str = "1280x720",
        image_path: Optional[str] = None,  # 新增：参考图路径
        style_params: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None
    ):
        self.prompt = prompt
        self.duration = duration
        self.resolution = resolution
        self.image_path = image_path
        self.style_params = style_params or {}
        self.seed = seed


class VideoGenerationResult:
    """视频生成结果"""
    def __init__(
        self,
        success: bool,
        video_url: Optional[str] = None,
        local_path: Optional[str] = None,
        duration: Optional[float] = None,
        resolution: Optional[str] = None,
        cost: Optional[float] = None,
        generation_time: Optional[float] = None,
        quality_score: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.video_url = video_url
        self.local_path = local_path
        self.duration = duration
        self.resolution = resolution
        self.cost = cost
        self.generation_time = generation_time
        self.quality_score = quality_score
        self.error_message = error_message
        self.metadata = metadata or {}


class BaseVideoGenerationClient(ABC):
    """视频生成API客户端基类"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """
        生成视频
        
        Args:
            request: 视频生成请求
            
        Returns:
            VideoGenerationResult: 生成结果
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        获取API能力信息
        
        Returns:
            Dict: 包含最大时长、成本、质量等信息
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查API是否可用
        
        Returns:
            bool: API是否可用
        """
        pass
    
    async def download_video(self, video_url: str, local_path: str) -> bool:
        """
        下载视频到本地
        
        Args:
            video_url: 视频URL
            local_path: 本地保存路径
            
        Returns:
            bool: 是否下载成功
        """
        try:
            import aiohttp
            import aiofiles
            
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        self.logger.info(f"视频下载成功: {local_path}")
                        return True
                    else:
                        self.logger.error(f"视频下载失败，状态码: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"视频下载异常: {str(e)}")
            return False
    
    def estimate_cost(self, duration: float) -> float:
        """
        估算生成成本
        
        Args:
            duration: 视频时长(秒)
            
        Returns:
            float: 预估成本(美元)
        """
        capabilities = self.get_capabilities()
        return duration * capabilities.get('cost_per_second', 0.1)
    
    def validate_request(self, request: VideoGenerationRequest) -> tuple[bool, str]:
        """
        验证请求参数
        
        Args:
            request: 视频生成请求
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        capabilities = self.get_capabilities()
        
        # 检查时长限制
        max_duration = capabilities.get('max_duration', 10)
        if request.duration > max_duration:
            return False, f"视频时长超过限制: {request.duration}s > {max_duration}s"
        
        # 检查提示词长度
        if not request.prompt or len(request.prompt.strip()) == 0:
            return False, "提示词不能为空"
        
        if len(request.prompt) > 1000:
            return False, "提示词过长，请控制在1000字符以内"
        
        return True, ""
