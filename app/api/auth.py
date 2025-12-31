from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.crud import user as crud_user
from app.schemas import user as user_schemas
from app.schemas import token as token_schemas
from app.core import security
from app.core.config import settings
from app.utils.database import get_db
from app.api import deps

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login/access-token", response_model=token_schemas.Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=user_schemas.User)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: user_schemas.UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud_user.create_user(db, user=user_in)
    return user

@router.post("/test-token", response_model=user_schemas.User)
def test_token(current_user: user_schemas.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user
