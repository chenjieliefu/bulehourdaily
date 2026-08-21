"""公开接口的最小安全边界。"""
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.api import collect, events, reports
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_token
from app.main import app
from app.models import DailyReport, InviteCode, User
from app.models.enums import ReportStatus
from app.services.seed import seed_configured_invite_codes


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/collect/run", None),
        ("/api/v1/events/extract", None),
        ("/api/v1/reports/generate", None),
        ("/api/v1/subscriptions", {"user_id": 1, "months": 1}),
    ],
)
def test_internal_write_endpoints_require_login(client, monkeypatch, path, payload):
    """未登录不能触发采集、AI 任务或人工开通订阅。"""
    now = datetime.utcnow()
    monkeypatch.setattr(
        collect,
        "collect_all",
        lambda _db: {
            "started_at": now,
            "finished_at": now,
            "total_sources": 0,
            "success": 0,
            "failed": 0,
            "new_items": 0,
            "results": [],
        },
    )
    monkeypatch.setattr(events, "run_in_background", lambda _kind: 1)
    monkeypatch.setattr(reports, "run_in_background", lambda _kind: 1)

    response = (
        client.post(path, json=payload) if payload is not None else client.post(path)
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/collect/run", None),
        ("/api/v1/events/extract", None),
        ("/api/v1/reports/generate", None),
        ("/api/v1/subscriptions", {"user_id": 1, "months": 1}),
    ],
)
def test_internal_write_endpoints_reject_non_operator(db, client, path, payload):
    """普通内测用户也不能执行运营动作。"""
    user = User(email="boundary-user@example.com", password_hash="test", is_operator=False)
    db.add(user)
    db.commit()
    token = create_token(user.id)

    response = client.post(
        path,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_operator_can_still_use_internal_write_endpoints(db, client, monkeypatch):
    """加上门禁后，运营者原有工作流仍然可用。"""
    operator = User(
        email="boundary-operator@example.com",
        password_hash="test",
        is_operator=True,
    )
    target = User(email="subscription-target@example.com", password_hash="test")
    db.add_all([operator, target])
    db.commit()
    token = create_token(operator.id)
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.utcnow()
    monkeypatch.setattr(
        collect,
        "collect_all",
        lambda _db: {
            "started_at": now,
            "finished_at": now,
            "total_sources": 0,
            "success": 0,
            "failed": 0,
            "new_items": 0,
            "results": [],
        },
    )
    monkeypatch.setattr(events, "run_in_background", lambda _kind: 1)
    monkeypatch.setattr(reports, "run_in_background", lambda _kind: 2)

    assert client.post("/api/v1/collect/run", headers=headers).status_code == 200
    assert client.post("/api/v1/events/extract", headers=headers).status_code == 202
    assert client.post("/api/v1/reports/generate", headers=headers).status_code == 202
    assert (
        client.post(
            "/api/v1/subscriptions",
            json={"user_id": target.id, "months": 1},
            headers=headers,
        ).status_code
        == 201
    )


def test_public_reports_only_expose_published(db, client):
    draft = DailyReport(
        report_date=date(2026, 8, 20),
        status=ReportStatus.draft,
        summary="内部草稿",
    )
    published = DailyReport(
        report_date=date(2026, 8, 21),
        status=ReportStatus.published,
        summary="公开日报",
        published_at=datetime.utcnow(),
    )
    db.add_all([draft, published])
    db.commit()

    response = client.get("/api/v1/reports")

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [published.id]
    assert client.get(f"/api/v1/reports/{published.id}").status_code == 200
    assert client.get(f"/api/v1/reports/{draft.id}").status_code == 404


def test_fixed_test_invites_are_disabled_by_default(db, monkeypatch):
    monkeypatch.setattr(settings, "seed_test_invite_codes", False)

    assert seed_configured_invite_codes(db) == 0
    assert db.query(InviteCode).count() == 0


def test_fixed_test_invites_require_explicit_opt_in(db, monkeypatch):
    monkeypatch.setattr(settings, "seed_test_invite_codes", True)

    assert seed_configured_invite_codes(db) == 5
    assert db.query(InviteCode).count() == 5
