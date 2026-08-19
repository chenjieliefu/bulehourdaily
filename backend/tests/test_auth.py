"""注册/登录测试。"""
import pytest
from fastapi import HTTPException

from app.models import InviteCode
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
