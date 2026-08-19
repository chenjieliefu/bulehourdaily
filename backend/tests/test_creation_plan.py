"""创作方案生成测试（mock 模式）。"""
import pytest

from app.models import CreationPlan, CreatorProfile, InviteCode, PersonalizedTopic
from app.services.auth import register
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


def test_generate_plan_overwrites(db, source_factory, item_factory):
    user, topic = _setup(db, source_factory, item_factory)
    generate_plan(db, user.id, topic.id)
    generate_plan(db, user.id, topic.id)
    assert db.query(CreationPlan).count() == 1


def test_generate_plan_wrong_user_raises(db, source_factory, item_factory):
    user, topic = _setup(db, source_factory, item_factory)
    db.add(InviteCode(code="C2"))
    db.commit()
    other = register(db, "x@y.com", "secret123", "C2")
    with pytest.raises(ValueError):
        generate_plan(db, other.id, topic.id)
