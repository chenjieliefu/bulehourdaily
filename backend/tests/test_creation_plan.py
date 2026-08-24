"""创作方案生成测试（mock 模式）。"""
import pytest

from app.models import CreationPlan, CreatorProfile, InviteCode, PersonalizedTopic
from app.services.auth import register
from app.core.config import settings
from app.services import creation_plan
from app.services.creation_plan import generate_plan
from app.services.event_extraction import extract_events
from app.services.personalization import generate_personalized


def _setup(db, source_factory, item_factory):
    db.add(InviteCode(code="C1"))
    db.commit()
    user = register(db, "a@b.com", "secret123", "C1")
    db.add(
        CreatorProfile(
            user_id=user.id, positioning="定位", audience="观众", persona="人设",
            style="风格", video_length="60秒", forbidden="禁区",
        )
    )
    db.commit()
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)
    generate_personalized(db, user.id)
    topic = db.query(PersonalizedTopic).first()
    return user, topic


def test_generate_plan_creates(db, source_factory, item_factory):
    user, topic = _setup(db, source_factory, item_factory)
    result = generate_plan(db, user.id, topic.id)
    plan = db.get(CreationPlan, result["plan_id"])
    assert plan.core_viewpoint
    assert len(plan.hooks) == 2
    assert len(plan.titles) == 2
    assert plan.risks


def test_generate_plan_preserves_existing(db, source_factory, item_factory):
    user, topic = _setup(db, source_factory, item_factory)
    first = generate_plan(db, user.id, topic.id)
    second = generate_plan(db, user.id, topic.id)
    assert first["plan_id"] == second["plan_id"]
    assert second["status"] == "already_generated"
    assert db.query(CreationPlan).count() == 1


def test_invalid_model_result_does_not_create_plan(db, source_factory, item_factory, monkeypatch):
    user, topic = _setup(db, source_factory, item_factory)
    monkeypatch.setattr(creation_plan.llm, "is_available", lambda: True)
    monkeypatch.setattr(creation_plan.llm, "complete_json", lambda *_args, **_kwargs: {})

    with pytest.raises(creation_plan.CreationPlanQualityError):
        generate_plan(db, user.id, topic.id)
    assert db.query(CreationPlan).count() == 0


def test_production_never_falls_back_to_mock(db, source_factory, item_factory, monkeypatch):
    user, topic = _setup(db, source_factory, item_factory)
    monkeypatch.setattr(settings, "app_env", "prod")

    with pytest.raises(creation_plan.CreationPlanQualityError, match="模型暂不可用"):
        generate_plan(db, user.id, topic.id)
    assert db.query(CreationPlan).count() == 0


def test_generate_plan_wrong_user_raises(db, source_factory, item_factory):
    user, topic = _setup(db, source_factory, item_factory)
    db.add(InviteCode(code="C2"))
    db.commit()
    other = register(db, "x@y.com", "secret123", "C2")
    with pytest.raises(ValueError):
        generate_plan(db, other.id, topic.id)
