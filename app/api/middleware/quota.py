"""
配额检查中间件
用于在API调用前验证用户配额
"""
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging

from app.models.user import User
from app.api import deps
from app.utils.database import get_db

logger = logging.getLogger(__name__)


class QuotaExceededException(HTTPException):
    """配额超限异常"""
    def __init__(self, detail: str, quota_type: str, current: int, limit: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": detail,
                "quota_type": quota_type,
                "current_usage": current,
                "quota_limit": limit,
                "error_code": "QUOTA_EXCEEDED"
            }
        )


async def check_video_generation_quota(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    检查视频生成配额

    在视频生成API之前使用此依赖
    """
    # 检查用户是否激活
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # 检查是否需要重置配额
    if current_user.quota_reset_date and datetime.utcnow() > current_user.quota_reset_date:
        logger.info(f"Resetting quota for user {current_user.id}")
        current_user.reset_monthly_quota()
        db.commit()
        db.refresh(current_user)

    # 检查视频生成配额
    if current_user.video_generated >= current_user.video_quota:
        logger.warning(
            f"User {current_user.id} exceeded video quota: "
            f"{current_user.video_generated}/{current_user.video_quota}"
        )
        raise QuotaExceededException(
            detail=f"Monthly video generation quota exceeded. "
                   f"You have used {current_user.video_generated} out of {current_user.video_quota} videos. "
                   f"Quota resets on {current_user.quota_reset_date.strftime('%Y-%m-%d')}. "
                   f"Please upgrade your plan to generate more videos.",
            quota_type="video_generation",
            current=current_user.video_generated,
            limit=current_user.video_quota
        )

    return current_user


async def check_storage_quota(
    file_size_mb: float,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    检查存储空间配额

    在文件上传API之前使用此依赖
    参数：file_size_mb - 文件大小（MB）
    """
    # 检查存储配额
    if current_user.storage_used_mb + file_size_mb > current_user.storage_quota_mb:
        available = current_user.storage_quota_remaining_mb
        raise QuotaExceededException(
            detail=f"Storage quota exceeded. "
                   f"File size: {file_size_mb:.2f}MB, Available: {available:.2f}MB. "
                   f"Please delete old files or upgrade your plan.",
            quota_type="storage",
            current=int(current_user.storage_used_mb),
            limit=current_user.storage_quota_mb
        )

    return current_user


async def check_api_calls_quota(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    检查API调用配额

    在需要限制API调用的接口前使用此依赖
    """
    # 检查是否需要重置配额
    if current_user.quota_reset_date and datetime.utcnow() > current_user.quota_reset_date:
        current_user.reset_monthly_quota()
        db.commit()
        db.refresh(current_user)

    # 检查API调用配额
    if current_user.api_calls_used >= current_user.api_calls_quota:
        logger.warning(
            f"User {current_user.id} exceeded API calls quota: "
            f"{current_user.api_calls_used}/{current_user.api_calls_quota}"
        )
        raise QuotaExceededException(
            detail=f"Monthly API calls quota exceeded. "
                   f"You have used {current_user.api_calls_used} out of {current_user.api_calls_quota} calls. "
                   f"Quota resets on {current_user.quota_reset_date.strftime('%Y-%m-%d')}.",
            quota_type="api_calls",
            current=current_user.api_calls_used,
            limit=current_user.api_calls_quota
        )

    return current_user


def increment_video_count(user: User, db: Session):
    """增加视频生成计数"""
    user.increment_video_count()
    db.commit()
    logger.info(f"User {user.id} video count: {user.video_generated}/{user.video_quota}")


def increment_api_calls(user: User, db: Session, count: int = 1):
    """增加API调用计数"""
    user.increment_api_calls(count)
    db.commit()
    logger.debug(f"User {user.id} API calls: {user.api_calls_used}/{user.api_calls_quota}")


def add_storage_usage(user: User, db: Session, size_mb: float):
    """增加存储使用量"""
    user.add_storage_usage(size_mb)
    db.commit()
    logger.info(f"User {user.id} storage: {user.storage_used_mb:.2f}/{user.storage_quota_mb}MB")
