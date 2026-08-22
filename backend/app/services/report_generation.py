"""通用日报生成编排。

选题选择是确定性的：只选「事件时间距今 ≤ 新鲜门槛」的事件，不足放宽，宁缺毋滥。
建议发布时机 = 事件时间 + 热度窗口，转成绝对时间展示。
LLM 只负责「写内容」，不负责「选哪些事件」。
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import (
    DailyReport,
    EventEvidence,
    HotBrief,
    HotEvent,
    TopicRecommendation,
)
from app.models.enums import EventStatus, ReportStatus
from . import llm

_BJ = ZoneInfo("Asia/Shanghai")
_PROMPT = (Path(__file__).resolve().parent / "prompts" / "report_generation.md").read_text(encoding="utf-8")


def _hours_ago(dt: datetime | None, now: datetime) -> float:
    if dt is None:
        return 999.0
    return (now - dt).total_seconds() / 3600


def _deadline_str(first_seen_at: datetime) -> str:
    """事件时间 + 热度窗口 → 北京时间的绝对截止时间字符串。"""
    aware_utc = first_seen_at.replace(tzinfo=timezone.utc)
    bj = aware_utc.astimezone(_BJ) + timedelta(hours=settings.hot_window_hours)
    return f"{bj.month}月{bj.day}日 {bj.hour:02d}:{bj.minute:02d}"


def _event_lines(db: Session, events: list[HotEvent]) -> list[str]:
    ev_ids = [e.id for e in events]
    links: dict[int, list[str]] = {}
    if ev_ids:
        for ev in db.query(EventEvidence).filter(EventEvidence.hot_event_id.in_(ev_ids)).all():
            links.setdefault(ev.hot_event_id, []).append(ev.source_item.url)

    lines = []
    for e in events:
        ts = e.first_seen_at.strftime("%Y-%m-%d %H:%M") if e.first_seen_at else "未知"
        link_str = " | ".join(links.get(e.id, [])[:3])
        lines.append(
            f"id={e.id} | 事件时间={ts} | 可信度={e.credibility_label.value} | "
            f"标题={e.title} | 摘要={e.summary} | 证据={link_str}"
        )
    return lines


def _build_prompt(db: Session, topic_events: list[HotEvent], brief_events: list[HotEvent]) -> str:
    parts = ["## 选题事件（写完整选题建议）"]
    parts.extend(_event_lines(db, topic_events))
    parts.append("## 速览事件（只写一句话摘要）")
    parts.extend(_event_lines(db, brief_events))
    return "\n".join(parts)


def _mock_report(topic_events: list[HotEvent], brief_events: list[HotEvent]) -> dict:
    topics = []
    for e in topic_events:
        topics.append(
            {
                "event_id": e.id,
                "title": f"[模拟选题] {e.title[:60]}",
                "what_happened": e.summary[:300],
                "why_now": "[模拟] 值得关注的理由（接入真实 Key 后由模型生成）",
                "angle": "[模拟] 通用切入角度",
                "hook": "[模拟] 前三秒钩子",
                "structure": "[模拟] 60-90 秒结构",
                "visual": "[模拟] 画面/演示建议",
                "publish_reason": "趁热度最高",
            }
        )
    briefs = [{"event_id": e.id, "summary": e.summary[:200]} for e in brief_events]
    return {
        "summary": "[模拟] 今日海外 AI 动态一句话摘要（接入真实 Key 后由模型生成）",
        "topics": topics,
        "briefs": briefs,
    }


def generate_report(
    db: Session,
    *,
    report_date: date | None = None,
    event_from: datetime | None = None,
    event_before: datetime | None = None,
) -> dict:
    target_date = report_date or datetime.now(_BJ).date()
    existing_report = (
        db.query(DailyReport)
        .filter(DailyReport.report_date == target_date)
        .first()
    )
    if existing_report is not None and existing_report.status == ReportStatus.published:
        raise ValueError("当日日报已经发布，请先下架后再重新生成")

    published_topic_event_ids = {
        event_id
        for (event_id,) in db.query(TopicRecommendation.hot_event_id)
        .join(DailyReport, TopicRecommendation.report_id == DailyReport.id)
        .filter(
            DailyReport.status == ReportStatus.published,
            DailyReport.report_date < target_date,
        )
        .all()
    }
    published_brief_event_ids = {
        event_id
        for (event_id,) in db.query(HotBrief.hot_event_id)
        .join(DailyReport, HotBrief.report_id == DailyReport.id)
        .filter(
            DailyReport.status == ReportStatus.published,
            DailyReport.report_date < target_date,
        )
        .all()
    }
    already_published_event_ids = published_topic_event_ids | published_brief_event_ids

    query = db.query(HotEvent).filter(HotEvent.status != EventStatus.archived)
    if already_published_event_ids:
        query = query.filter(HotEvent.id.notin_(already_published_event_ids))
    if event_from is not None:
        query = query.filter(HotEvent.first_seen_at >= event_from)
    if event_before is not None:
        query = query.filter(HotEvent.first_seen_at < event_before)
    events = (
        query
        .order_by(HotEvent.sort_score.desc())
        .limit(15)
        .all()
    )
    if not events:
        raise ValueError("没有候选热点事件，请先执行「提取事件」")

    now = utcnow()
    fresh = [e for e in events if _hours_ago(e.first_seen_at, now) <= settings.topic_fresh_hours]
    if len(fresh) < 3:
        fresh = [
            e for e in events
            if _hours_ago(e.first_seen_at, now) <= settings.topic_fresh_relax_hours
        ]

    topic_events = fresh[:3]
    topic_ids = {e.id for e in topic_events}
    brief_events = [e for e in events if e.id not in topic_ids][:7]

    user_prompt = _build_prompt(db, topic_events, brief_events)
    if llm.is_available():
        data = llm.complete_json(_PROMPT, user_prompt)
    else:
        data = _mock_report(topic_events, brief_events)

    topics_by_event = {t.get("event_id"): t for t in data.get("topics", [])}

    today = target_date
    report = existing_report
    if report is None:
        report = DailyReport(report_date=today, status=ReportStatus.draft)
        db.add(report)
        db.flush()
    else:
        db.query(TopicRecommendation).filter(TopicRecommendation.report_id == report.id).delete()
        db.query(HotBrief).filter(HotBrief.report_id == report.id).delete()

    report.summary = str(data.get("summary") or "")[:1000]
    report.updated_at = utcnow()

    for idx, event in enumerate(topic_events, start=1):
        t = topics_by_event.get(event.id, {})
        reason = str(t.get("publish_reason") or "趁热度最高").strip()
        time_window = f"建议 {_deadline_str(event.first_seen_at)} 前发布，{reason}"
        db.add(
            TopicRecommendation(
                report_id=report.id,
                hot_event_id=event.id,
                title=str(t.get("title") or "")[:300] or event.title[:300],
                what_happened=str(t.get("what_happened") or "") or event.summary[:2000],
                why_now=str(t.get("why_now") or ""),
                angle=str(t.get("angle") or ""),
                hook=str(t.get("hook") or ""),
                structure=str(t.get("structure") or ""),
                visual=str(t.get("visual") or ""),
                time_window=time_window,
                order_index=idx,
            )
        )

    for idx, b in enumerate(
        [b for b in data.get("briefs", []) if b.get("event_id") in {e.id for e in brief_events}][:7],
        start=1,
    ):
        db.add(
            HotBrief(
                report_id=report.id,
                hot_event_id=b["event_id"],
                summary=str(b.get("summary") or "")[:500],
                order_index=idx,
            )
        )

    for e in topic_events:
        e.status = EventStatus.selected
    for e in brief_events:
        e.status = EventStatus.brief

    db.commit()
    return {
        "report_id": report.id,
        "topics": len(topic_events),
        "briefs": len(
            [b for b in data.get("briefs", []) if b.get("event_id") in {e.id for e in brief_events}][:7]
        ),
    }
