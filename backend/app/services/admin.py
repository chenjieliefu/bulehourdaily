"""轻量质检操作：通过/拒绝/编辑/补充选题、发布日报。"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import (
    DailyReport,
    EventEvidence,
    HotEvent,
    SourceItem,
    TopicRecommendation,
)
from app.models.enums import EventStatus, ReportStatus
from . import llm
from .report_generation import _deadline_str, _hours_ago

_BJ = ZoneInfo("Asia/Shanghai")
_TOPIC_PROMPT = (Path(__file__).resolve().parent / "prompts" / "single_topic.md").read_text(encoding="utf-8")


def _today() -> datetime:
    return datetime.now(_BJ).date()


def _renumber(db: Session, report_id: int) -> None:
    """重新给选题编号 1..N，保持连续。"""
    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report_id)
        .order_by(TopicRecommendation.order_index, TopicRecommendation.id)
        .all()
    )
    for i, t in enumerate(topics, start=1):
        t.order_index = i


def approve_topic(db: Session, topic_id: int) -> TopicRecommendation:
    topic = db.get(TopicRecommendation, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    topic.reviewed = True
    db.commit()
    db.refresh(topic)
    return topic


def reject_topic(db: Session, topic_id: int) -> None:
    topic = db.get(TopicRecommendation, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    report_id = topic.report_id
    db.delete(topic)
    db.flush()
    _renumber(db, report_id)
    db.commit()


def edit_topic(db: Session, topic_id: int, data: dict) -> TopicRecommendation:
    topic = db.get(TopicRecommendation, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    for key, value in data.items():
        if value is not None:
            setattr(topic, key, str(value)[:3000])
    db.commit()
    db.refresh(topic)
    return topic


def _mock_topic(event: HotEvent) -> dict:
    return {
        "title": f"[模拟选题] {event.title[:60]}",
        "what_happened": event.summary[:300],
        "why_now": "[模拟] 值得关注的理由",
        "angle": "[模拟] 通用切入角度",
        "hook": "[模拟] 前三秒钩子",
        "structure": "[模拟] 60-90 秒结构",
        "visual": "[模拟] 画面建议",
        "publish_reason": "趁热度最高",
    }


def add_topic_from_event(db: Session, event_id: int) -> TopicRecommendation:
    event = db.get(HotEvent, event_id)
    if event is None:
        raise ValueError("事件不存在")

    report = db.query(DailyReport).filter(DailyReport.report_date == _today()).first()
    if report is None:
        report = DailyReport(report_date=_today(), status=ReportStatus.draft)
        db.add(report)
        db.flush()

    event_text = (
        f"id={event.id} | 事件时间={event.first_seen_at} | 可信度={event.credibility_label.value} | "
        f"标题={event.title} | 摘要={event.summary}"
    )
    if llm.is_available():
        data = llm.complete_json(_TOPIC_PROMPT, event_text, max_tokens=3000)
    else:
        data = _mock_topic(event)

    existing_count = (
        db.query(TopicRecommendation).filter(TopicRecommendation.report_id == report.id).count()
    )
    if existing_count >= 3:
        raise ValueError("最多 3 个主选题，请先拒绝一个再补充")

    reason = str(data.get("publish_reason") or "趁热度最高").strip()
    time_window = f"建议 {_deadline_str(event.first_seen_at)} 前发布，{reason}"

    topic = TopicRecommendation(
        report_id=report.id,
        hot_event_id=event.id,
        title=str(data.get("title") or "")[:300] or event.title[:300],
        what_happened=str(data.get("what_happened") or "") or event.summary[:2000],
        why_now=str(data.get("why_now") or ""),
        angle=str(data.get("angle") or ""),
        hook=str(data.get("hook") or ""),
        structure=str(data.get("structure") or ""),
        visual=str(data.get("visual") or ""),
        time_window=time_window,
        order_index=existing_count + 1,
        reviewed=True,
    )
    db.add(topic)
    db.flush()
    _renumber(db, report.id)
    db.commit()
    db.refresh(topic)
    return topic


def publish_report(db: Session) -> DailyReport:
    report = db.query(DailyReport).filter(DailyReport.report_date == _today()).first()
    if report is None:
        raise ValueError("今日日报不存在，请先生成")
    unreviewed = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id, TopicRecommendation.reviewed.is_(False))
        .count()
    )
    if unreviewed > 0:
        raise ValueError(f"还有 {unreviewed} 个选题未质检，不能发布")
    if report.status != ReportStatus.published:
        report.status = ReportStatus.published
        report.published_at = utcnow()
        db.commit()
    return report


def candidate_events(db: Session, exclude_event_ids: set[int], limit: int = 10) -> list[HotEvent]:
    now = utcnow()
    events = (
        db.query(HotEvent)
        .filter(HotEvent.status != EventStatus.archived)
        .order_by(HotEvent.sort_score.desc())
        .limit(30)
        .all()
    )
    fresh = [e for e in events if _hours_ago(e.first_seen_at, now) <= settings.topic_fresh_relax_hours]
    return [e for e in fresh if e.id not in exclude_event_ids][:limit]
