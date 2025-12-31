"""
LLM适配器基类 - 定义统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator
import logging

logger = logging.getLogger(__name__)

class BaseLLMAdapter(ABC):
    """
    LLM适配器基类
    定义统一的调用接口，支持不同的底层实现

    重要原则:
    1. 适配器负责处理提供商特定的响应格式
    2. 返回统一的、标准化的数据结构
    3. Service 层不应该知道具体提供商的实现细节
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.available = False
        self._setup()

    @abstractmethod
    def _setup(self) -> None:
        """初始化适配器"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查适配器是否可用"""
        pass

    @abstractmethod
    def call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用LLM API（同步）

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            统一格式的响应:
            {
                "success": bool,
                "content": str,
                "provider": str,
                "model": str,
                "usage": dict,
                "error": str
            }
        """
        pass

    def stream_call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Iterator[str]:
        """
        流式调用LLM API

        重要: 适配器必须返回文本字符串的迭代器，而不是原始响应对象！
        每个适配器负责从提供商特定的响应格式中提取文本。

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            文本字符串片段（不是对象！）

        默认实现: 降级到普通调用
        子类可以重写以提供真正的流式支持
        """
        logger.warning(f"适配器 {self.name} 不支持流式调用，降级为普通调用")
        result = self.call(messages, **kwargs)
        if result.get("success"):
            yield result.get("content", "")
        else:
            logger.error(f"降级调用失败: {result.get('error')}")
            yield ""

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    def simple_call(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """简化调用接口"""
        messages = [{"role": "user", "content": prompt}]
        return self.call(messages, **kwargs)
    
    def get_info(self) -> Dict[str, Any]:
        """获取适配器信息"""
        return {
            "name": self.name,
            "available": self.is_available(),
            "config": self.config
        }
