"""日报生成编排测试（mock 模式）。"""
import pytest

from app.models import DailyReport, HotBrief, TopicRecommendation
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
