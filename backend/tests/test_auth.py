"""注册/登录测试。"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.auth import get_authenticated_user
from app.models import InviteCode, User
from app.core.security import hash_password
from app.schemas.auth import RegisterRequest
from app.services.auth import login, register


def _invite(db, code="ABC123"):
    c = InviteCode(code=code)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def test_register_ok(db):
    _invite(db)
    user = register(db, "A@B.com", "secret123", "ABC123")
    assert user.email == "a@b.com"  # 邮箱统一小写
    assert db.query(InviteCode).filter_by(code="ABC123").first().used is True


def test_register_invalid_code(db):
    with pytest.raises(HTTPException) as e:
        register(db, "a@b.com", "secret123", "NOPE")
    assert e.value.status_code == 400


def test_register_reused_code(db):
    _invite(db)
    register(db, "a@b.com", "secret123", "ABC123")
    with pytest.raises(HTTPException):
        register(db, "c@d.com", "secret123", "ABC123")


def test_register_duplicate_email(db):
    _invite(db, "C1")
    _invite(db, "C2")
    register(db, "a@b.com", "secret123", "C1")
    with pytest.raises(HTTPException) as e:
        register(db, "a@b.com", "secret123", "C2")
    assert e.value.status_code == 409


def test_login_ok(db):
    _invite(db)
    register(db, "a@b.com", "secret123", "ABC123")
    user = login(db, "a@b.com", "secret123")
    assert user.email == "a@b.com"


def test_login_wrong_password(db):
    _invite(db)
    register(db, "a@b.com", "secret123", "ABC123")
    with pytest.raises(HTTPException):
        login(db, "a@b.com", "wrong")


def test_authenticated_user_returns_server_side_role(db):
    """工作台必须以令牌在服务端对应的真实角色为准，不能只信前端缓存。"""
    user = User(
        email="operator@example.com",
        password_hash=hash_password("secret123"),
        is_operator=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    result = get_authenticated_user(user)

    assert result.id == user.id
    assert result.email == "operator@example.com"
    assert result.is_operator is True


def test_register_request_rejects_password_with_space():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="abc 123", invite_code="ABC123")


def test_register_request_rejects_password_with_non_ascii():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.com", password="密码abc", invite_code="ABC123")


def test_register_request_accepts_ascii_password():
    req = RegisterRequest(email="a@b.com", password="Abc123!@#", invite_code="ABC123")
    assert req.password == "Abc123!@#"
