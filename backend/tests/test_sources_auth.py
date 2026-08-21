"""信息源写操作鉴权测试（接口层）。"""
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_token
from app.main import app
from app.models import Source, User
from app.models.enums import SourceType


def test_sources_write_requires_operator(db):
    normal = User(email="normal@example.com", password_hash="test", is_operator=False)
    operator = User(email="operator@example.com", password_hash="test", is_operator=True)
    db.add_all([normal, operator])
    db.flush()
    source = Source(name="src", type=SourceType.rss, url="https://example.com/src")
    db.add(source)
    db.commit()
    db.refresh(source)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        # 未登录 → 401
        assert client.patch(
            f"/api/v1/sources/{source.id}", json={"enabled": False}
        ).status_code == 401

        # 普通用户 → 403
        normal_token = create_token(normal.id)
        assert client.patch(
            f"/api/v1/sources/{source.id}",
            json={"enabled": False},
            headers={"Authorization": f"Bearer {normal_token}"},
        ).status_code == 403

        # 运营者 → 200，且真实更新成功
        operator_token = create_token(operator.id)
        resp = client.patch(
            f"/api/v1/sources/{source.id}",
            json={"enabled": False},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
    finally:
        app.dependency_overrides.clear()
