"""日报生成编排测试（mock 模式）。"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.time import utcnow
from app.models import DailyReport, HotBrief, HotEvent, TopicRecommendation
from app.models.enums import CredibilityLabel, EventStatus, ReportStatus
from app.services.event_extraction import extract_events
from app.services.report_generation import generate_report


def test_generate_report_creates_topics(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)  # 6 条 → 3 个事件

    result = generate_report(db)

    assert result["report_id"] is not None
    assert result["topics"] == 3
    report = db.get(DailyReport, result["report_id"])
    assert report is not None
    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id)
        .all()
    )
    assert len(topics) == 3
    assert all(t.hook and t.structure for t in topics)


def test_regenerate_same_day_overwrites(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    first = generate_report(db)
    second = generate_report(db)

    # 同一天只保留一份日报，选题不翻倍
    assert first["report_id"] == second["report_id"]
    assert db.query(DailyReport).count() == 1
    assert db.query(TopicRecommendation).count() == 3
    assert db.query(HotBrief).count() == 0  # 事件不足 3 个以上，速览为 0


def test_published_report_cannot_be_overwritten(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    first = generate_report(db)
    report = db.get(DailyReport, first["report_id"])
    report.status = ReportStatus.published
    db.commit()
    original_topic_ids = [
        row.id
        for row in db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id)
        .order_by(TopicRecommendation.id)
        .all()
    ]

    with pytest.raises(ValueError, match="已经发布"):
        generate_report(db)

    current_topic_ids = [
        row.id
        for row in db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id)
        .order_by(TopicRecommendation.id)
        .all()
    ]
    assert current_topic_ids == original_topic_ids


def test_generate_without_events_raises(db):
    with pytest.raises(ValueError):
        generate_report(db)


def test_events_from_older_published_reports_are_not_reused(db):
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    old_event = HotEvent(
        title="已经发布过的事件",
        summary="旧摘要",
        credibility_label=CredibilityLabel.official,
        status=EventStatus.selected,
        first_seen_at=utcnow(),
    )
    new_event = HotEvent(
        title="今天首次出现的事件",
        summary="新摘要",
        credibility_label=CredibilityLabel.official,
        status=EventStatus.candidate,
        first_seen_at=utcnow(),
    )
    old_report = DailyReport(
        report_date=today - timedelta(days=1),
        status=ReportStatus.published,
        summary="上一期日报",
        published_at=utcnow(),
    )
    db.add_all([old_event, new_event, old_report])
    db.flush()
    db.add(
        TopicRecommendation(
            report_id=old_report.id,
            hot_event_id=old_event.id,
            title="旧选题",
            what_happened="旧内容",
            why_now="昨天",
            angle="旧角度",
            hook="旧钩子",
            structure="旧结构",
            visual="旧画面",
            time_window="已过期",
            order_index=1,
            reviewed=True,
        )
    )
    db.commit()

    result = generate_report(db, report_date=today)

    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == result["report_id"])
        .all()
    )
    assert [topic.hot_event_id for topic in topics] == [new_event.id]


def test_expired_events_are_not_topics(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    # 把所有事件改成 3 天前（过期）
    old = utcnow() - timedelta(days=3)
    for e in db.query(HotEvent).all():
        e.first_seen_at = old
    db.commit()

    result = generate_report(db)
    # 宁缺毋滥：过期事件不进选题，但进速览
    assert result["topics"] == 0
    assert result["briefs"] == 3


def test_time_window_is_absolute_with_reason(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)

    result = generate_report(db)
    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == result["report_id"])
        .all()
    )
    assert topics
    tw = topics[0].time_window
    assert tw.startswith("建议 ")
    assert "前发布" in tw
    assert "趁热度最高" in tw  # mock 的 reason
