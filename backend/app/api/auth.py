"""鉴权接口：注册、登录。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_token
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserRead
from app.services.auth import login, register

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register(db, payload.email, payload.password, payload.invite_code)
    return AuthResponse(token=create_token(user.id), user=UserRead(id=user.id, email=user.email, is_operator=user.is_operator))


@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = login(db, payload.email, payload.password)
    return AuthResponse(token=create_token(user.id), user=UserRead(id=user.id, email=user.email, is_operator=user.is_operator))
