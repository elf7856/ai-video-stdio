from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.crud import user as crud_user
from app.schemas import user as user_schemas
from app.schemas.quota import UserQuota, QuotaUpdate
from app.utils.database import get_db
from app.api import deps
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("/", response_model=List[user_schemas.User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users. (Admin only)
    """
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=user_schemas.User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: user_schemas.UserCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user. (Admin only)
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud_user.create_user(db, user=user_in)
    return user

@router.get("/me", response_model=user_schemas.User)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/me/quota", response_model=UserQuota)
def read_user_quota(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user's quota information.
    """
    return UserQuota(
        video_quota=current_user.video_quota,
        video_generated=current_user.video_generated,
        video_quota_remaining=current_user.video_quota_remaining,
        storage_quota_mb=current_user.storage_quota_mb,
        storage_used_mb=current_user.storage_used_mb,
        storage_quota_remaining_mb=current_user.storage_quota_remaining_mb,
        api_calls_quota=current_user.api_calls_quota,
        api_calls_used=current_user.api_calls_used,
        api_calls_remaining=current_user.api_calls_remaining,
        quota_reset_date=current_user.quota_reset_date,
        is_quota_exceeded=current_user.is_quota_exceeded
    )

@router.get("/{user_id}", response_model=user_schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud_user.get_user(db, user_id=user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user

@router.post("/{user_id}/quota/reset")
def reset_user_quota(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Reset user's monthly quota. (Admin only)
    """
    user = crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.reset_monthly_quota()
    db.commit()
    db.refresh(user)

    return {"message": "Quota reset successfully", "user_id": user_id}

@router.patch("/{user_id}/quota", response_model=user_schemas.User)
def update_user_quota(
    user_id: int,
    quota_update: QuotaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update user's quota limits. (Admin only)
    """
    user = crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if quota_update.video_quota is not None:
        user.video_quota = quota_update.video_quota
    if quota_update.storage_quota_mb is not None:
        user.storage_quota_mb = quota_update.storage_quota_mb
    if quota_update.api_calls_quota is not None:
        user.api_calls_quota = quota_update.api_calls_quota

    db.commit()
    db.refresh(user)

    return user
