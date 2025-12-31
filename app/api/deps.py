from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.token import TokenPayload
from app.utils.database import get_db

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/auth/login/access-token",
    auto_error=False  # 允许无token访问
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud_user.get_user(db, user_id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(reusable_oauth2)
) -> Optional[User]:
    """
    获取当前用户（可选）
    如果没有token或token无效，返回None而不是抛出异常
    用于开发阶段或允许匿名访问的接口
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user = crud_user.get_user(db, user_id=token_data.sub)
        if user and user.is_active:
            return user
    except (JWTError, ValidationError):
        pass
    return None


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
