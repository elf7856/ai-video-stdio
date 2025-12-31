"""
LLM适配器层 - 统一接口，只使用 Google
"""

from .base import BaseLLMAdapter
from .google_adapter import GoogleAdapter

__all__ = [
    'BaseLLMAdapter',
    'GoogleAdapter'
]
