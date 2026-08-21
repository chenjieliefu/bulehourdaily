"""鉴权接口：注册、登录。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_token
from app.models import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserRead
from app.services.auth import get_current_user, login, register

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register(db, payload.email, payload.password, payload.invite_code)
    return AuthResponse(token=create_token(user.id), user=UserRead(id=user.id, email=user.email, is_operator=user.is_operator))


@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = login(db, payload.email, payload.password)
    return AuthResponse(token=create_token(user.id), user=UserRead(id=user.id, email=user.email, is_operator=user.is_operator))


@router.get("/me", response_model=UserRead)
def get_authenticated_user(user: User = Depends(get_current_user)):
    """返回令牌当前对应的服务端用户，供前端校准缓存角色。"""
    return UserRead(id=user.id, email=user.email, is_operator=user.is_operator)
