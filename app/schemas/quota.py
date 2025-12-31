from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class UserQuota(BaseModel):
    """用户配额信息"""
    # 视频配额
    video_quota: int
    video_generated: int
    video_quota_remaining: int

    # 存储配额
    storage_quota_mb: int
    storage_used_mb: float
    storage_quota_remaining_mb: float

    # API调用配额
    api_calls_quota: int
    api_calls_used: int
    api_calls_remaining: int

    # 配额重置日期
    quota_reset_date: datetime

    # 配额状态
    is_quota_exceeded: bool

    class Config:
        from_attributes = True

class QuotaUpdate(BaseModel):
    """配额更新请求（管理员使用）"""
    video_quota: Optional[int] = None
    storage_quota_mb: Optional[int] = None
    api_calls_quota: Optional[int] = None
