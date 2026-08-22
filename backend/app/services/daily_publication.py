"""每天 08:00 的公开日报生产与自动发布管线。"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import DailyReport, EventEvidence, HotBrief, TopicRecommendation
from app.models.enums import ReportStatus
from .collection import collect_all
from .event_extraction import extract_events
from .report_generation import generate_report

_BJ = ZoneInfo("Asia/Shanghai")
_REQUIRED_TOPIC_FIELDS = (
    "title",
    "what_happened",
    "why_now",
    "angle",
    "hook",
    "structure",
    "visual",
    "time_window",
)
_FORBIDDEN_MARKERS = ("[模拟]", "[模拟事件")


class DailyPublicationQualityError(ValueError):
    """日报未达到自动公开标准。"""


def previous_day_window(report_date: date) -> tuple[datetime, datetime]:
    """返回前一自然日在北京时间对应的 UTC 无时区半开区间。"""
    end_bj = datetime.combine(report_date, time.min, tzinfo=_BJ)
    start_bj = end_bj - timedelta(days=1)
    return (
        start_bj.astimezone(timezone.utc).replace(tzinfo=None),
        end_bj.astimezone(timezone.utc).replace(tzinfo=None),
    )


def _contains_forbidden_marker(value: str | None) -> bool:
    text = value or ""
    return any(marker in text for marker in _FORBIDDEN_MARKERS)


def validate_for_auto_publish(db: Session, report: DailyReport) -> list[str]:
    """返回阻止自动公开的问题；空列表代表通过。"""
    issues: list[str] = []
    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id)
        .order_by(TopicRecommendation.order_index)
        .all()
    )
    briefs = (
        db.query(HotBrief)
        .filter(HotBrief.report_id == report.id)
        .order_by(HotBrief.order_index)
        .all()
    )

    if not 1 <= len(topics) <= 3:
        issues.append(f"主选题数量必须为 1—3 条，当前为 {len(topics)} 条")
    if not (report.summary or "").strip():
        issues.append("日报摘要为空")
    if _contains_forbidden_marker(report.summary):
        issues.append("日报摘要包含模拟内容")

    event_ids = {topic.hot_event_id for topic in topics} | {brief.hot_event_id for brief in briefs}
    evidence_event_ids = {
        event_id
        for (event_id,) in db.query(EventEvidence.hot_event_id)
        .filter(EventEvidence.hot_event_id.in_(event_ids))
        .distinct()
        .all()
    } if event_ids else set()

    for index, topic in enumerate(topics, start=1):
        missing = [field for field in _REQUIRED_TOPIC_FIELDS if not str(getattr(topic, field) or "").strip()]
        if missing:
            issues.append(f"第 {index} 个主选题缺少字段：{', '.join(missing)}")
        if any(_contains_forbidden_marker(str(getattr(topic, field) or "")) for field in _REQUIRED_TOPIC_FIELDS):
            issues.append(f"第 {index} 个主选题包含模拟内容")
        if topic.hot_event_id not in evidence_event_ids:
            issues.append(f"第 {index} 个主选题没有原始证据")

    for index, brief in enumerate(briefs, start=1):
        if not (brief.summary or "").strip():
            issues.append(f"第 {index} 条速览摘要为空")
        if _contains_forbidden_marker(brief.summary):
            issues.append(f"第 {index} 条速览包含模拟内容")
        if brief.hot_event_id not in evidence_event_ids:
            issues.append(f"第 {index} 条速览没有原始证据")

    return issues


def run_daily_publication(db: Session, *, report_date: date | None = None) -> dict:
    """采集前一自然日内容，生成并自动公开当日日报；可安全重复执行。"""
    target_date = report_date or datetime.now(_BJ).date()
    existing = db.query(DailyReport).filter(DailyReport.report_date == target_date).first()
    if existing is not None and existing.status == ReportStatus.published:
        return {
            "report_id": existing.id,
            "report_date": target_date.isoformat(),
            "status": "already_published",
        }

    window_start, window_end = previous_day_window(target_date)
    collection = collect_all(db)
    extraction = extract_events(
        db,
        published_from=window_start,
        published_before=window_end,
    )
    generation = generate_report(
        db,
        report_date=target_date,
        event_from=window_start,
        event_before=window_end,
    )
    report = db.get(DailyReport, generation["report_id"])
    if report is None:
        raise RuntimeError("日报生成完成但未找到日报记录")

    issues = validate_for_auto_publish(db, report)
    if issues:
        raise DailyPublicationQualityError("；".join(issues))

    report.status = ReportStatus.published
    report.published_at = utcnow()
    db.commit()
    return {
        "report_id": report.id,
        "report_date": target_date.isoformat(),
        "status": "published",
        "topics": generation["topics"],
        "briefs": generation["briefs"],
        "events_created": extraction["events_created"],
        "new_items": collection.new_items,
    }
