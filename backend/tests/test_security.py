"""密码哈希与 JWT 测试。"""
from app.core.security import create_token, decode_token, hash_password, verify_password


def test_password_roundtrip():
    stored = hash_password("secret123")
    assert verify_password("secret123", stored)
    assert not verify_password("wrong", stored)


def test_password_salt_differs():
    assert hash_password("x") != hash_password("x")


def test_token_roundtrip():
    token = create_token(42)
    assert decode_token(token) == 42


def test_token_invalid():
    assert decode_token("bad.token.here") is None
    assert decode_token("") is None
