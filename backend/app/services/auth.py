"""注册、登录、当前用户依赖。"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.core.time import utcnow
from app.models import InviteCode, User


def register(db: Session, email: str, password: str, invite_code: str) -> User:
    email = email.strip().lower()
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(status_code=409, detail="该邮箱已注册")

    invite = db.query(InviteCode).filter(InviteCode.code == invite_code.strip()).first()
    if invite is None:
        raise HTTPException(status_code=400, detail="邀请码无效")
    if invite.used:
        raise HTTPException(status_code=400, detail="邀请码已被使用")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    invite.used = True
    invite.used_by = user.id
    invite.used_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return user


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    user_id = decode_token(authorization[len("Bearer "):])
    if user_id is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_current_operator(
    user: User = Depends(get_current_user),
) -> User:
    """运营者访问校验：登录用户必须是运营者账号。"""
    if not user.is_operator:
        raise HTTPException(status_code=403, detail="无运营者权限")
    return user
