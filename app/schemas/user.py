from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserTier

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    tier: UserTier = UserTier.FREE

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 配额信息（只读）
    video_quota: Optional[int] = None
    video_generated: Optional[int] = None
    storage_quota_mb: Optional[int] = None
    storage_used_mb: Optional[float] = None
    api_calls_quota: Optional[int] = None
    api_calls_used: Optional[int] = None
    quota_reset_date: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
