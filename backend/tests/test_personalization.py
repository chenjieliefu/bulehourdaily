"""个性化日报生成测试（mock 模式）。"""
from datetime import date, timedelta

import pytest

from app.models import (
    CreatorProfile,
    HotEvent,
    InviteCode,
    MailDelivery,
    PersonalizedReport,
    PersonalizedTopic,
    TopicFeedback,
)
from app.models.enums import FeedbackStatus
from app.core.config import settings
from app.services.auth import register
from app.services.event_extraction import extract_events
from app.services import personalization
from app.services.personalization import generate_personalized
from app.services.subscriptions import create_subscription


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


def test_regenerate_same_day_preserves_existing_report(db, source_factory, item_factory):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    first = generate_personalized(db, user.id)
    topic = db.query(PersonalizedTopic).filter_by(report_id=first["report_id"]).first()
    feedback = TopicFeedback(user_id=user.id, topic_id=topic.id, status=FeedbackStatus.want)
    db.add(feedback)
    db.commit()
    original_topic_ids = [row.id for row in db.query(PersonalizedTopic).filter_by(report_id=first["report_id"]).all()]

    second = generate_personalized(db, user.id)
    assert first["report_id"] == second["report_id"]
    assert second["status"] == "already_generated"
    assert db.query(PersonalizedReport).count() == 1
    assert [row.id for row in db.query(PersonalizedTopic).filter_by(report_id=first["report_id"]).all()] == original_topic_ids
    assert db.get(TopicFeedback, feedback.id).topic_id == topic.id


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


def test_generate_does_not_create_fake_mail_delivery(db, source_factory, item_factory):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    generate_personalized(db, user.id)
    assert db.query(MailDelivery).count() == 0


def test_invalid_model_result_does_not_consume_trial(db, source_factory, item_factory, monkeypatch):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    monkeypatch.setattr(personalization.llm, "is_available", lambda: True)
    monkeypatch.setattr(
        personalization.llm,
        "complete_json",
        lambda *_args, **_kwargs: {"summary": "", "reason": "", "topics": []},
    )

    with pytest.raises(personalization.PersonalizedQualityError):
        generate_personalized(db, user.id)
    assert db.query(PersonalizedReport).count() == 0


def test_existing_event_with_unsupported_scale_claim_is_not_recommended(
    db, source_factory, item_factory
):
    user = _user(db)
    _profile(db, user)
    source = source_factory()
    item_factory(
        source,
        title="'AI refuser' quit her dream job, and hopes others follow",
    )
    for i in range(5):
        item_factory(source, title=f"safe-{i}")
    extract_events(db)
    bad_event = db.query(HotEvent).order_by(HotEvent.id).first()
    bad_event.title = "AI 从业者辞职潮引关注"
    db.commit()

    result = generate_personalized(db, user.id)
    topics = (
        db.query(PersonalizedTopic)
        .filter(PersonalizedTopic.report_id == result["report_id"])
        .all()
    )

    assert result["topics"] == 2
    assert all(topic.hot_event_id != bad_event.id for topic in topics)


def test_personalized_rewrite_cannot_expand_single_case_into_wave(
    db, source_factory, item_factory, monkeypatch
):
    user = _user(db)
    _profile(db, user)
    source = source_factory()
    item_factory(
        source,
        title="'AI refuser' quit her dream job, and hopes others follow",
    )
    extract_events(db)
    event = db.query(HotEvent).one()
    monkeypatch.setattr(personalization.llm, "is_available", lambda: True)
    monkeypatch.setattr(
        personalization.llm,
        "complete_json",
        lambda *_args, **_kwargs: {
            "summary": "今日推荐",
            "reason": "适合你的观众",
            "topics": [
                {
                    "event_id": event.id,
                    "title": "AI 从业者辞职潮",
                    "what_happened": "一位 AI 从业者辞去工作。",
                    "why_now": "值得关注",
                    "angle": "个人选择",
                    "hook": "她为什么辞职？",
                    "structure": "三段式",
                    "visual": "新闻截图",
                    "publish_reason": "仍有讨论价值",
                    "recommendation_reason": "适合职场观众",
                }
            ],
        },
    )

    with pytest.raises(personalization.PersonalizedQualityError, match="扩大了原始证据范围"):
        generate_personalized(db, user.id)
    assert db.query(PersonalizedReport).count() == 0


def test_production_never_falls_back_to_mock(db, source_factory, item_factory, monkeypatch):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)
    monkeypatch.setattr(settings, "app_env", "prod")

    with pytest.raises(personalization.PersonalizedQualityError, match="模型暂不可用"):
        generate_personalized(db, user.id)
    assert db.query(PersonalizedReport).count() == 0


def test_active_subscription_bypasses_trial(db, source_factory, item_factory):
    user = _user(db)
    _profile(db, user)
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    today = date.today()
    for i in range(1, 4):  # 体验 3 份已用完
        db.add(PersonalizedReport(user_id=user.id, report_date=today - timedelta(days=i)))
    db.commit()

    create_subscription(db, user.id)  # 开通订阅后不再受限
    result = generate_personalized(db, user.id)
    assert result["report_id"] is not None
