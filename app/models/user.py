from sqlalchemy import Boolean, Column, Integer, String, Enum as SAEnum, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta
from app.utils.database import Base

class UserTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    tier = Column(SAEnum(UserTier), default=UserTier.FREE)

    # 配额管理字段
    video_quota = Column(Integer, default=10)  # 每月视频生成配额
    video_generated = Column(Integer, default=0)  # 当月已生成视频数
    storage_quota_mb = Column(Integer, default=1000)  # 存储空间配额（MB）
    storage_used_mb = Column(Float, default=0.0)  # 已使用存储空间
    api_calls_quota = Column(Integer, default=1000)  # API调用配额
    api_calls_used = Column(Integer, default=0)  # 已使用API调用数
    quota_reset_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))  # 配额重置日期

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def video_quota_remaining(self) -> int:
        """剩余视频配额"""
        return max(0, self.video_quota - self.video_generated)

    @property
    def storage_quota_remaining_mb(self) -> float:
        """剩余存储空间（MB）"""
        return max(0, self.storage_quota_mb - self.storage_used_mb)

    @property
    def api_calls_remaining(self) -> int:
        """剩余API调用数"""
        return max(0, self.api_calls_quota - self.api_calls_used)

    @property
    def is_quota_exceeded(self) -> bool:
        """是否超出配额"""
        return (self.video_generated >= self.video_quota or
                self.storage_used_mb >= self.storage_quota_mb or
                self.api_calls_used >= self.api_calls_quota)

    def can_generate_video(self) -> bool:
        """检查是否可以生成视频"""
        return self.video_generated < self.video_quota and self.is_active

    def increment_video_count(self):
        """增加视频生成计数"""
        self.video_generated += 1
        self.updated_at = datetime.utcnow()

    def increment_api_calls(self, count: int = 1):
        """增加API调用计数"""
        self.api_calls_used += count
        self.updated_at = datetime.utcnow()

    def add_storage_usage(self, size_mb: float):
        """增加存储使用量"""
        self.storage_used_mb += size_mb
        self.updated_at = datetime.utcnow()

    def reset_monthly_quota(self):
        """重置月度配额"""
        self.video_generated = 0
        self.api_calls_used = 0
        self.quota_reset_date = datetime.utcnow() + timedelta(days=30)
        self.updated_at = datetime.utcnow()

    def set_quota_by_tier(self):
        """根据会员等级设置配额"""
        tier_quotas = {
            UserTier.FREE: {
                "video_quota": 10,
                "storage_quota_mb": 1000,  # 1GB
                "api_calls_quota": 1000
            },
            UserTier.PRO: {
                "video_quota": 100,
                "storage_quota_mb": 10000,  # 10GB
                "api_calls_quota": 10000
            },
            UserTier.ENTERPRISE: {
                "video_quota": 1000,
                "storage_quota_mb": 100000,  # 100GB
                "api_calls_quota": 100000
            }
        }

        quotas = tier_quotas.get(self.tier, tier_quotas[UserTier.FREE])
        self.video_quota = quotas["video_quota"]
        self.storage_quota_mb = quotas["storage_quota_mb"]
        self.api_calls_quota = quotas["api_calls_quota"]
        self.updated_at = datetime.utcnow()
