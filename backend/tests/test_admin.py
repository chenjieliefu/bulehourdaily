"""轻量质检测试（mock 模式）。"""
import pytest

from app.models import DailyReport, HotEvent, TopicRecommendation
from app.models.enums import ReportStatus
from app.services import admin as admin_svc
from app.services.event_extraction import extract_events
from app.services.report_generation import generate_report


def _setup(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)
    result = generate_report(db)
    report = db.get(DailyReport, result["report_id"])
    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id)
        .all()
    )
    return report, topics


def test_publish_requires_reviewed(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    with pytest.raises(ValueError, match="未质检"):
        admin_svc.publish_report(db)


def test_approve_then_publish(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    for t in topics:
        admin_svc.approve_topic(db, t.id)
    admin_svc.publish_report(db)
    db.refresh(report)
    assert report.status == ReportStatus.published
    assert report.published_at is not None


def test_reject_topic(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    admin_svc.reject_topic(db, topics[0].id)
    assert db.get(TopicRecommendation, topics[0].id) is None


def test_edit_topic(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    t = admin_svc.edit_topic(db, topics[0].id, {"title": "改过的标题", "hook": "新钩子"})
    assert t.title == "改过的标题"
    assert t.hook == "新钩子"


def test_add_topic_from_event(db, source_factory, item_factory):
    src = source_factory()
    for i in range(6):
        item_factory(src, title=f"t{i}")
    extract_events(db)
    event = db.query(HotEvent).first()

    topic = admin_svc.add_topic_from_event(db, event.id)
    assert topic.reviewed is True  # 运营者选定即视为已通过
    report = db.get(DailyReport, topic.report_id)
    assert report is not None
    assert topic.time_window.startswith("建议 ")
