"""通用日报生成编排：已排序事件 → 通用日报（选题 + 速览）。"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

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


def _build_events_prompt(db: Session, events: list[HotEvent]) -> str:
    ev_ids = [e.id for e in events]
    links: dict[int, list[str]] = {}
    for ev in db.query(EventEvidence).filter(EventEvidence.hot_event_id.in_(ev_ids)).all():
        links.setdefault(ev.hot_event_id, []).append(ev.source_item.url)

    lines = []
    for e in events:
        link_str = " | ".join(links.get(e.id, [])[:3])
        lines.append(
            f"id={e.id} | 可信度={e.credibility_label.value} | 标题={e.title} | 摘要={e.summary} | 证据链接={link_str}"
        )
    return "\n".join(lines)


def _mock_report(events: list[HotEvent]) -> dict:
    topics = []
    for e in events[:3]:
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
                "time_window": "[模拟] 24 小时内",
            }
        )
    briefs = [{"event_id": e.id, "summary": e.summary[:200]} for e in events[3:8]]
    return {
        "summary": "[模拟] 今日海外 AI 动态一句话摘要（接入真实 Key 后由模型生成）",
        "topics": topics,
        "briefs": briefs,
    }


def generate_report(db: Session) -> dict:
    events = (
        db.query(HotEvent)
        .filter(HotEvent.status != EventStatus.archived)
        .order_by(HotEvent.sort_score.desc())
        .limit(10)
        .all()
    )
    if not events:
        raise ValueError("没有候选热点事件，请先执行「提取事件」")

    user_prompt = _build_events_prompt(db, events)
    if llm.is_available():
        data = llm.complete_json(_PROMPT, user_prompt)
    else:
        data = _mock_report(events)

    event_ids = {e.id for e in events}
    topics_data = [t for t in data.get("topics", []) if t.get("event_id") in event_ids][:3]
    briefs_data = [b for b in data.get("briefs", []) if b.get("event_id") in event_ids][:7]

    today = datetime.now(_BJ).date()
    report = db.query(DailyReport).filter(DailyReport.report_date == today).first()
    if report is None:
        report = DailyReport(report_date=today, status=ReportStatus.draft)
        db.add(report)
        db.flush()
    else:
        # 同一天重新生成：清除旧选题与速览，再写入
        db.query(TopicRecommendation).filter(TopicRecommendation.report_id == report.id).delete()
        db.query(HotBrief).filter(HotBrief.report_id == report.id).delete()

    report.summary = str(data.get("summary") or "")[:1000]
    report.updated_at = utcnow()

    for idx, t in enumerate(topics_data, start=1):
        db.add(
            TopicRecommendation(
                report_id=report.id,
                hot_event_id=t["event_id"],
                title=str(t.get("title") or "")[:300] or "未命名选题",
                what_happened=str(t.get("what_happened") or ""),
                why_now=str(t.get("why_now") or ""),
                angle=str(t.get("angle") or ""),
                hook=str(t.get("hook") or ""),
                structure=str(t.get("structure") or ""),
                visual=str(t.get("visual") or ""),
                time_window=str(t.get("time_window") or ""),
                order_index=idx,
            )
        )
    for idx, b in enumerate(briefs_data, start=1):
        db.add(
            HotBrief(
                report_id=report.id,
                hot_event_id=b["event_id"],
                summary=str(b.get("summary") or "")[:500],
                order_index=idx,
            )
        )

    topic_event_ids = {t["event_id"] for t in topics_data}
    brief_event_ids = {b["event_id"] for b in briefs_data}
    for e in events:
        if e.id in topic_event_ids:
            e.status = EventStatus.selected
        elif e.id in brief_event_ids:
            e.status = EventStatus.brief

    db.commit()
    return {"report_id": report.id, "topics": len(topics_data), "briefs": len(briefs_data)}
