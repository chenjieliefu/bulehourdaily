"""08:00 自动发布管线测试。"""
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.models import DailyReport, EventEvidence, HotEvent, TopicRecommendation
from app.models.enums import CredibilityLabel, ReportStatus
from app.services import daily_publication as daily_mod


def _draft_with_topic(db, source_factory, item_factory, report_date: date, *, evidence: bool = True):
    source = source_factory(name="daily-publication-source")
    item = item_factory(source, title="真实来源内容")
    item.published_at = datetime(2026, 8, 22, 4, 0)
    event = HotEvent(
        title="真实事件",
        summary="真实事件摘要",
        credibility_label=CredibilityLabel.official,
        first_seen_at=item.published_at,
    )
    report = DailyReport(
        report_date=report_date,
        status=ReportStatus.draft,
        summary="今天有一条经过验证的重要动态。",
    )
    db.add_all([event, report])
    db.flush()
    topic = TopicRecommendation(
        report_id=report.id,
        hot_event_id=event.id,
        title="真实选题",
        what_happened="发生了一件真实且可验证的事情。",
        why_now="它发生在前一自然日，值得今天关注。",
        angle="从实际影响切入。",
        hook="这件事刚刚发生。",
        structure="背景、变化、影响、结论。",
        visual="展示官方来源和产品画面。",
        time_window="建议今天发布。",
        order_index=1,
    )
    db.add(topic)
    if evidence:
        db.add(EventEvidence(hot_event_id=event.id, source_item_id=item.id))
    db.commit()
    return report


def _stub_pipeline(monkeypatch, report_id: int):
    monkeypatch.setattr(daily_mod, "collect_all", lambda _db: SimpleNamespace(new_items=1))
    monkeypatch.setattr(
        daily_mod,
        "extract_events",
        lambda _db, **_kwargs: {"events_created": 1, "candidates": 1},
    )
    monkeypatch.setattr(
        daily_mod,
        "generate_report",
        lambda _db, **_kwargs: {"report_id": report_id, "topics": 1, "briefs": 0},
    )


def test_previous_day_window_uses_beijing_natural_day():
    start, end = daily_mod.previous_day_window(date(2026, 8, 23))

    assert start == datetime(2026, 8, 21, 16, 0)
    assert end == datetime(2026, 8, 22, 16, 0)


def test_valid_one_topic_report_is_automatically_published(
    db, source_factory, item_factory, monkeypatch
):
    old_report = DailyReport(
        report_date=date(2026, 8, 22),
        status=ReportStatus.published,
        summary="上一期日报",
        published_at=datetime(2026, 8, 22, 0, 0),
    )
    db.add(old_report)
    db.commit()
    report = _draft_with_topic(db, source_factory, item_factory, date(2026, 8, 23))
    _stub_pipeline(monkeypatch, report.id)

    result = daily_mod.run_daily_publication(db, report_date=date(2026, 8, 23))

    db.refresh(report)
    db.refresh(old_report)
    assert result["status"] == "published"
    assert result["topics"] == 1
    assert report.status == ReportStatus.published
    assert report.published_at is not None
    assert old_report.status == ReportStatus.published


def test_quality_failure_keeps_previous_public_report(
    db, source_factory, item_factory, monkeypatch
):
    old_report = DailyReport(
        report_date=date(2026, 8, 22),
        status=ReportStatus.published,
        summary="仍应公开的上一期日报",
        published_at=datetime(2026, 8, 22, 0, 0),
    )
    db.add(old_report)
    db.commit()
    report = _draft_with_topic(
        db,
        source_factory,
        item_factory,
        date(2026, 8, 23),
        evidence=False,
    )
    _stub_pipeline(monkeypatch, report.id)

    with pytest.raises(daily_mod.DailyPublicationQualityError, match="没有原始证据"):
        daily_mod.run_daily_publication(db, report_date=date(2026, 8, 23))

    db.refresh(report)
    db.refresh(old_report)
    assert report.status == ReportStatus.draft
    assert report.published_at is None
    assert old_report.status == ReportStatus.published


def test_published_date_is_idempotent_and_skips_pipeline(db, monkeypatch):
    report = DailyReport(
        report_date=date(2026, 8, 23),
        status=ReportStatus.published,
        summary="已经发布",
        published_at=datetime(2026, 8, 23, 0, 0),
    )
    db.add(report)
    db.commit()

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("已经发布的日期不应重复执行生产管线")

    monkeypatch.setattr(daily_mod, "collect_all", should_not_run)
    monkeypatch.setattr(daily_mod, "extract_events", should_not_run)
    monkeypatch.setattr(daily_mod, "generate_report", should_not_run)

    result = daily_mod.run_daily_publication(db, report_date=report.report_date)

    assert result == {
        "report_id": report.id,
        "report_date": "2026-08-23",
        "status": "already_published",
    }


def test_mock_content_never_passes_auto_publish_quality_gate(
    db, source_factory, item_factory
):
    report = _draft_with_topic(db, source_factory, item_factory, date(2026, 8, 23))
    report.summary = "[模拟] 这不是可公开内容"
    db.commit()

    issues = daily_mod.validate_for_auto_publish(db, report)

    assert "日报摘要包含模拟内容" in issues
