"""日报生成编排测试（mock 模式）。"""
from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.models import DailyReport, HotBrief, HotEvent, TopicRecommendation
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


def test_generate_without_events_raises(db):
    with pytest.raises(ValueError):
        generate_report(db)


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
