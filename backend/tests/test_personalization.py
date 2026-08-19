"""个性化日报生成测试（mock 模式）。"""
from datetime import date, timedelta

import pytest

from app.models import CreatorProfile, InviteCode, PersonalizedReport, PersonalizedTopic
from app.services.auth import register
from app.services.event_extraction import extract_events
from app.services.personalization import generate_personalized


def _user(db):
    db.add(InviteCode(code="CODE1"))
    db.commit()
    return register(db, "a@b.com", "secret123", "CODE1")


def _profile(db, user):
    p = CreatorProfile(
        user_id=user.id,
        positioning="AI 工具测评",
        audience="想学 AI 的普通人",
        persona="技术博主",
        style="口语化、爱打比方",
        video_length="60 秒",
        forbidden="不碰政治、不碰医疗",
    )
    db.add(p)
    db.commit()
    return p


def test_generate_requires_profile(db):
    user = _user(db)
    with pytest.raises(ValueError):
        generate_personalized(db, user.id)


def test_generate_creates_report_and_topics(db, source_factory, item_factory):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)  # mock 生成 3 个事件

    result = generate_personalized(db, user.id)
    assert result["report_id"] is not None
    assert result["topics"] == 3

    report = db.get(PersonalizedReport, result["report_id"])
    assert report.user_id == user.id
    topics = db.query(PersonalizedTopic).filter_by(report_id=report.id).all()
    assert len(topics) == 3
    # 每个个性化选题都带「为什么推荐给你」
    assert all(t.recommendation_reason for t in topics)
    # 建议发布时机为绝对时间
    assert all(t.time_window.startswith("建议 ") for t in topics)


def test_regenerate_same_day_overwrites(db, source_factory, item_factory):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    first = generate_personalized(db, user.id)
    second = generate_personalized(db, user.id)
    assert first["report_id"] == second["report_id"]
    assert db.query(PersonalizedReport).count() == 1


def test_trial_limit_three_reports(db, source_factory, item_factory):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    today = date.today()
    for i in range(1, 4):  # 过去 3 天各一份，今天还没生成
        db.add(PersonalizedReport(user_id=user.id, report_date=today - timedelta(days=i)))
    db.commit()

    with pytest.raises(ValueError, match="体验次数"):
        generate_personalized(db, user.id)
