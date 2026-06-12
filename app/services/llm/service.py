"""
统一LLM服务 - 简洁版本
去除冗余，保留适配器架构的灵活性
"""

import time
import logging
from typing import Dict, Any, List, Optional, Iterator
from enum import Enum

from .adapters import (
    BaseLLMAdapter,
    GoogleAdapter
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """LLM 提供商类型"""
    GOOGLE = "google"


class LLMService:
    """
    统一LLM服务管理器

    特性:
    1. 支持多个 Adapter（但默认使用 Google）
    2. 统一的重试和错误处理逻辑
    3. 自动降级切换（失败时尝试其他 Adapter）
    4. 简洁的 API 接口

    使用方式:
        llm = LLMService()  # 默认使用 Google
        result = llm.call([{"role": "user", "content": "Hello"}])

        # 或指定提供商
        llm = LLMService(provider=ProviderType.GOOGLE)
    """

    def __init__(
        self,
        provider: ProviderType = ProviderType.GOOGLE,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 LLM 服务

        Args:
            provider: 主要使用的提供商
            config: 配置字典（可选）
        """
        self.config = config or self._get_default_config()
        self.primary_provider = provider
        self.adapters: Dict[str, BaseLLMAdapter] = {}
        self.performance_stats: Dict[str, Dict] = {}

        self._init_adapters()

        # 获取可用的适配器
        available = self.get_available_adapters()
        if not available:
            logger.warning("没有可用的 LLM 适配器，请检查 API 密钥配置")
        else:
            logger.info(f"可用适配器: {available}, 主要使用: {provider.value}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "timeout": 10,
            "max_retries": 3,
            "retry_delay": 2,
            "auto_fallback": True,  # 失败时自动切换到其他提供商
            "models": {
                "google": "gemini-3-flash"
            },
            "default_params": {
                "max_tokens": 2000,
                "temperature": 0.3
            }
        }

    def _init_adapters(self) -> None:
        """初始化所有适配器（但只有配置了 API 密钥的才可用）"""
        adapter_configs = {
            ProviderType.GOOGLE: {
                "model": self.config["models"].get("google", "gemini-3-flash"),
                "timeout": self.config["timeout"],
                **self.config["default_params"]
            }
        }

        # 尝试初始化每个适配器
        adapter_classes = {
            ProviderType.GOOGLE: GoogleAdapter
        }

        for provider_type, adapter_class in adapter_classes.items():
            try:
                adapter = adapter_class(config=adapter_configs[provider_type])
                if adapter.is_available():
                    self.adapters[provider_type.value] = adapter
                    self.performance_stats[provider_type.value] = {
                        "success_count": 0,
                        "failure_count": 0,
                        "total_time": 0.0,
                        "avg_time": 0.0
                    }
                    logger.debug(f"适配器 {provider_type.value} 初始化成功")
                else:
                    logger.debug(f"适配器 {provider_type.value} 不可用（可能缺少 API 密钥）")
            except Exception as e:
                logger.warning(f"初始化适配器 {provider_type.value} 失败: {e}")

    def get_available_adapters(self) -> List[str]:
        """获取所有可用的适配器名称"""
        return list(self.adapters.keys())

    def get_adapter(self, provider: Optional[str] = None) -> Optional[BaseLLMAdapter]:
        """
        获取指定的适配器

        Args:
            provider: 提供商名称，None 则使用主要提供商

        Returns:
            适配器实例，如果不可用则返回 None
        """
        if provider is None:
            provider = self.primary_provider.value

        return self.adapters.get(provider)

    def call(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_count: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 LLM API（统一接口）

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            provider: 指定提供商，None 则使用主要提供商
            timeout: 超时时间（秒）
            retry_count: 重试次数
            **kwargs: 其他参数（如 max_tokens, temperature）

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
        timeout = timeout or self.config["timeout"]
        retry_count = retry_count or self.config["max_retries"]
        retry_delay = self.config["retry_delay"]

        # 确定要尝试的提供商列表
        providers_to_try = [provider or self.primary_provider.value]

        # 如果启用了自动降级，添加其他可用提供商
        if self.config["auto_fallback"]:
            for p in self.get_available_adapters():
                if p not in providers_to_try:
                    providers_to_try.append(p)

        last_error = None

        # 按顺序尝试每个提供商
        for current_provider in providers_to_try:
            adapter = self.get_adapter(current_provider)

            if not adapter:
                logger.warning(f"适配器 {current_provider} 不可用，跳过")
                continue

            # 带重试的调用
            for attempt in range(retry_count):
                try:
                    start_time = time.time()
                    logger.info(f"调用 {current_provider} (尝试 {attempt + 1}/{retry_count})")

                    result = adapter.call(
                        messages=messages,
                        timeout=timeout,
                        **kwargs
                    )

                    elapsed = time.time() - start_time

                    # 更新性能统计
                    if result.get("success"):
                        self._update_stats(current_provider, True, elapsed)
                        logger.info(f"✅ {current_provider} 调用成功 (耗时: {elapsed:.2f}s)")
                        return result
                    else:
                        self._update_stats(current_provider, False, elapsed)
                        last_error = result.get("error", "未知错误")
                        logger.warning(f"❌ {current_provider} 调用失败: {last_error}")

                        # 如果不是最后一次重试，等待后重试
                        if attempt < retry_count - 1:
                            time.sleep(retry_delay)

                except Exception as e:
                    last_error = str(e)
                    logger.error(f"❌ {current_provider} 异常: {last_error}")

                    # 如果不是最后一次重试，等待后重试
                    if attempt < retry_count - 1:
                        time.sleep(retry_delay)

        # 所有提供商都失败
        return {
            "success": False,
            "content": "",
            "provider": "none",
            "model": "",
            "usage": {},
            "error": f"所有提供商调用失败，最后错误: {last_error}"
        }

    def stream_call(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        流式调用 LLM API

        适配器层负责处理提供商特定的响应格式，
        Service 层只负责调度和错误处理。

        Args:
            messages: 消息列表
            provider: 指定提供商
            **kwargs: 其他参数

        Yields:
            文本字符串片段
        """
        adapter = self.get_adapter(provider)

        if not adapter:
            provider_name = provider or self.primary_provider.value
            logger.error(f"适配器 {provider_name} 不可用")
            yield ""
            return

        try:
            logger.info(f"流式调用 {adapter.name}")

            # 直接yield from适配器返回的文本迭代器
            # 适配器已经处理了提供商特定的响应格式
            yield from adapter.stream_call(messages, **kwargs)

        except Exception as e:
            logger.error(f"流式调用失败: {e}", exc_info=True)
            yield ""

    def simple_call(
        self,
        prompt: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        简化的调用接口（单个 prompt）

        Args:
            prompt: 用户提示词
            provider: 指定提供商
            **kwargs: 其他参数

        Returns:
            同 call() 方法的返回值
        """
        messages = [{"role": "user", "content": prompt}]
        return self.call(messages, provider, **kwargs)

    def _update_stats(self, provider: str, success: bool, elapsed: float) -> None:
        """更新性能统计"""
        if provider not in self.performance_stats:
            return

        stats = self.performance_stats[provider]

        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1

        stats["total_time"] += elapsed
        total_calls = stats["success_count"] + stats["failure_count"]
        if total_calls > 0:
            stats["avg_time"] = stats["total_time"] / total_calls

    def get_stats(self) -> Dict[str, Dict]:
        """获取性能统计信息"""
        return self.performance_stats.copy()

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            {
                "healthy": bool,
                "available_adapters": List[str],
                "primary_provider": str,
                "stats": Dict
            }
        """
        available = self.get_available_adapters()

        return {
            "healthy": len(available) > 0,
            "available_adapters": available,
            "primary_provider": self.primary_provider.value,
            "primary_available": self.primary_provider.value in available,
            "stats": self.get_stats()
        }

llm_service = LLMService(provider=ProviderType.GOOGLE)

def get_llm_service() -> LLMService:
    """获取全局 LLM 服务实例"""
    return llm_service
