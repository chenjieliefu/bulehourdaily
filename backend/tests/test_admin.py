"""轻量质检测试（mock 模式）。"""
import pytest

from app.api import reports as reports_api
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
    assert all(topic.is_published is True for topic in topics)


def test_publish_requires_at_least_one_topic(db):
    db.add(DailyReport(report_date=admin_svc._today(), status=ReportStatus.draft))
    db.commit()

    with pytest.raises(ValueError, match="至少保留 1 个"):
        admin_svc.publish_report(db)


def test_unpublish_keeps_draft_and_requires_full_rereview(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    for topic in topics:
        admin_svc.approve_topic(db, topic.id)
    admin_svc.publish_report(db)

    admin_svc.unpublish_report(db)

    db.refresh(report)
    for topic in topics:
        db.refresh(topic)
    assert report.status == ReportStatus.draft
    assert report.published_at is None
    assert all(topic.reviewed is False for topic in topics)
    assert all(topic.is_published is False for topic in topics)
    with pytest.raises(ValueError, match="未质检"):
        admin_svc.publish_report(db)


def test_published_report_must_be_unpublished_before_edit(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    for topic in topics:
        admin_svc.approve_topic(db, topic.id)
    admin_svc.publish_report(db)

    with pytest.raises(ValueError, match="请先下架"):
        admin_svc.edit_topic(db, topics[0].id, {"title": "不应直接改动"})

    db.refresh(topics[0])
    assert topics[0].title != "不应直接改动"


def test_published_topic_can_be_approved_without_unpublishing(
    db, source_factory, item_factory,
):
    report, topics = _setup(db, source_factory, item_factory)
    for topic in topics:
        admin_svc.approve_topic(db, topic.id)
    admin_svc.publish_report(db)
    target = topics[0]
    target.reviewed = False
    db.commit()

    admin_svc.approve_topic(db, target.id)

    db.refresh(report)
    db.refresh(target)
    assert report.status == ReportStatus.published
    assert target.is_published is True
    assert target.reviewed is True


def test_unpublish_one_topic_keeps_report_and_record_published(
    db, source_factory, item_factory,
):
    report, topics = _setup(db, source_factory, item_factory)
    for topic in topics:
        admin_svc.approve_topic(db, topic.id)
    admin_svc.publish_report(db)

    admin_svc.unpublish_topic(db, topics[1].id)

    db.refresh(report)
    for topic in topics:
        db.refresh(topic)
    assert report.status == ReportStatus.published
    assert db.get(TopicRecommendation, topics[1].id) is not None
    assert topics[1].is_published is False
    assert topics[1].reviewed is False
    assert topics[0].is_published is True
    assert topics[2].is_published is True

    public_detail = reports_api._report_detail(db, report)
    assert [topic.id for topic in public_detail.topics] == [topics[0].id, topics[2].id]
    assert [topic.order_index for topic in public_detail.topics] == [1, 2]


def test_unpublished_topic_can_be_edited_reviewed_and_republished(
    db, source_factory, item_factory,
):
    report, topics = _setup(db, source_factory, item_factory)
    for topic in topics:
        admin_svc.approve_topic(db, topic.id)
    admin_svc.publish_report(db)
    target = topics[1]
    admin_svc.unpublish_topic(db, target.id)

    with pytest.raises(ValueError, match="尚未通过复核"):
        admin_svc.republish_topic(db, target.id)

    admin_svc.edit_topic(db, target.id, {"title": "修订后的主题"})
    db.refresh(target)
    assert target.title == "修订后的主题"
    assert target.reviewed is False
    assert target.is_published is False

    admin_svc.approve_topic(db, target.id)
    admin_svc.republish_topic(db, target.id)

    db.refresh(report)
    db.refresh(target)
    assert report.status == ReportStatus.published
    assert target.reviewed is True
    assert target.is_published is True
    public_detail = reports_api._report_detail(db, report)
    assert [topic.id for topic in public_detail.topics] == [topic.id for topic in topics]
    assert public_detail.topics[1].title == "修订后的主题"


def test_last_published_topic_requires_unpublishing_whole_report(
    db, source_factory, item_factory,
):
    report, topics = _setup(db, source_factory, item_factory)
    for topic in topics:
        admin_svc.approve_topic(db, topic.id)
    admin_svc.publish_report(db)
    admin_svc.unpublish_topic(db, topics[0].id)
    admin_svc.unpublish_topic(db, topics[1].id)

    with pytest.raises(ValueError, match="最后一个"):
        admin_svc.unpublish_topic(db, topics[2].id)

    db.refresh(report)
    db.refresh(topics[2])
    assert report.status == ReportStatus.published
    assert topics[2].is_published is True


def test_remove_topic(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    admin_svc.remove_topic(db, topics[0].id)
    assert db.get(TopicRecommendation, topics[0].id) is None


def test_edit_topic(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    t = admin_svc.edit_topic(db, topics[0].id, {"title": "改过的标题", "hook": "新钩子"})
    assert t.title == "改过的标题"
    assert t.hook == "新钩子"


def test_editing_reviewed_draft_requires_review_again(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    admin_svc.approve_topic(db, topics[0].id)

    topic = admin_svc.edit_topic(db, topics[0].id, {"title": "修订后重新复核"})

    assert topic.reviewed is False


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


def test_add_topic_limited_to_three(db, source_factory, item_factory):
    src = source_factory(max_per_day=10)
    for i in range(10):
        item_factory(src, title=f"t{i}")
    extract_events(db)  # 5 个事件
    events = db.query(HotEvent).limit(3).all()
    for e in events:
        admin_svc.add_topic_from_event(db, e.id)
    e4 = db.query(HotEvent).offset(3).first()
    with pytest.raises(ValueError, match="最多 3 个"):
        admin_svc.add_topic_from_event(db, e4.id)


def test_remove_renumbers(db, source_factory, item_factory):
    report, topics = _setup(db, source_factory, item_factory)
    admin_svc.remove_topic(db, topics[0].id)
    remaining = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id)
        .order_by(TopicRecommendation.order_index)
        .all()
    )
    assert [t.order_index for t in remaining] == [1, 2]
