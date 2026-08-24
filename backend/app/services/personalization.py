"""个性化日报生成：按画像从共享热点池重选 3 个选题、重写角度。"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import (
    CreatorProfile,
    EventEvidence,
    HotEvent,
    PersonalizedReport,
    PersonalizedTopic,
    SourceItem,
)
from app.models.enums import EventStatus
from . import llm
from .event_extraction import has_unsupported_scale_claim
from .report_generation import _deadline_str, _hours_ago
from .subscriptions import has_active_subscription

_BJ = ZoneInfo("Asia/Shanghai")
_PROMPT = (Path(__file__).resolve().parent / "prompts" / "personalization.md").read_text(encoding="utf-8")
_REQUIRED_TOPIC_FIELDS = (
    "title",
    "what_happened",
    "why_now",
    "angle",
    "hook",
    "structure",
    "visual",
    "recommendation_reason",
)
_FORBIDDEN_MARKERS = ("[模拟]", "[模拟个性化选题]")


class PersonalizedQualityError(ValueError):
    """个性化日报未达到可交付标准。"""


def _profile_text(p: CreatorProfile) -> str:
    return (
        f"账号定位：{p.positioning}\n目标观众：{p.audience}\n人设：{p.persona}\n"
        f"表达风格：{p.style}\n常见视频长度：{p.video_length}\n内容禁区：{p.forbidden}"
    )


def _events_text(db: Session, events: list[HotEvent]) -> str:
    ev_ids = [e.id for e in events]
    links: dict[int, list[str]] = {}
    if ev_ids:
        for ev in db.query(EventEvidence).filter(EventEvidence.hot_event_id.in_(ev_ids)).all():
            links.setdefault(ev.hot_event_id, []).append(ev.source_item.url)
    lines = []
    for e in events:
        ts = e.first_seen_at.strftime("%Y-%m-%d %H:%M") if e.first_seen_at else "未知"
        lines.append(
            f"id={e.id} | 事件时间={ts} | 可信度={e.credibility_label.value} | "
            f"标题={e.title} | 摘要={e.summary} | 证据={ ' | '.join(links.get(e.id, [])[:2]) }"
        )
    return "\n".join(lines)


def _mock(profile: CreatorProfile, events: list[HotEvent]) -> dict:
    topics = []
    for e in events[:3]:
        topics.append(
            {
                "event_id": e.id,
                "title": f"[模拟个性化选题] {e.title[:50]}",
                "what_happened": e.summary[:300],
                "why_now": "[模拟] 值得关注的理由（接入真实 Key 后由模型生成）",
                "angle": "[模拟] 贴合你账号定位的切入角度",
                "hook": "[模拟] 前三秒钩子",
                "structure": "[模拟] 60-90 秒结构",
                "visual": "[模拟] 画面建议",
                "publish_reason": "趁热度最高",
                "recommendation_reason": f"[模拟] 你的定位是「{profile.positioning[:20]}」，这个适合你的观众",
            }
        )
    return {
        "summary": "[模拟] 根据你的账号定位，今天推荐这些选题",
        "reason": f"[模拟] 因为你的定位是「{profile.positioning[:30]}」，所以推荐这些",
        "topics": topics,
    }


def _contains_forbidden_marker(value: object) -> bool:
    text = str(value or "")
    return any(marker in text for marker in _FORBIDDEN_MARKERS)


def _evidence_items_by_event(
    db: Session,
    event_ids: set[int],
) -> dict[int, list[SourceItem]]:
    result: dict[int, list[SourceItem]] = {}
    if not event_ids:
        return result
    for evidence in (
        db.query(EventEvidence)
        .filter(EventEvidence.hot_event_id.in_(event_ids))
        .all()
    ):
        result.setdefault(evidence.hot_event_id, []).append(evidence.source_item)
    return result


def _validated_topics(db: Session, data: dict, candidates: list[HotEvent]) -> list[dict]:
    """在写库和占用体验次数之前校验模型结果。"""
    issues: list[str] = []
    summary = str(data.get("summary") or "").strip()
    reason = str(data.get("reason") or "").strip()
    if not summary:
        issues.append("日报摘要为空")
    if not reason:
        issues.append("整份推荐理由为空")

    raw_topics = data.get("topics")
    if not isinstance(raw_topics, list):
        raw_topics = []
    candidate_ids = {event.id for event in candidates}
    evidence_items = _evidence_items_by_event(db, candidate_ids)
    topics: list[dict] = []
    seen_event_ids: set[int] = set()
    for raw in raw_topics:
        if not isinstance(raw, dict):
            issues.append("选题格式错误")
            continue
        event_id = raw.get("event_id")
        if event_id not in candidate_ids:
            issues.append("选题引用了候选池之外的事件")
            continue
        if event_id in seen_event_ids:
            issues.append("同一事件被重复推荐")
            continue
        seen_event_ids.add(event_id)
        topics.append(raw)

    if not 1 <= len(topics) <= 3:
        issues.append(f"个性化选题数量必须为 1—3 条，当前为 {len(topics)} 条")

    evidence_event_ids = {
        event_id
        for (event_id,) in db.query(EventEvidence.hot_event_id)
        .filter(EventEvidence.hot_event_id.in_(seen_event_ids))
        .distinct()
        .all()
    } if seen_event_ids else set()

    for index, topic in enumerate(topics, start=1):
        missing = [field for field in _REQUIRED_TOPIC_FIELDS if not str(topic.get(field) or "").strip()]
        if missing:
            issues.append(f"第 {index} 个选题缺少字段：{', '.join(missing)}")
        if topic.get("event_id") not in evidence_event_ids:
            issues.append(f"第 {index} 个选题没有原始证据")
        elif has_unsupported_scale_claim(
            topic.get("title"),
            topic.get("what_happened"),
            evidence_items.get(topic["event_id"], []),
        ):
            issues.append(f"第 {index} 个选题扩大了原始证据范围")

    if settings.app_env == "prod":
        values = [summary, reason]
        values.extend(topic.get(field) for topic in topics for field in _REQUIRED_TOPIC_FIELDS)
        if any(_contains_forbidden_marker(value) for value in values):
            issues.append("个性化日报包含模拟内容")

    if issues:
        raise PersonalizedQualityError("；".join(issues))
    return topics


def generate_personalized(db: Session, user_id: int) -> dict:
    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user_id).first()
    if profile is None:
        raise ValueError("请先填写创作者画像")

    today = datetime.now(_BJ).date()
    existing = (
        db.query(PersonalizedReport)
        .filter(PersonalizedReport.user_id == user_id, PersonalizedReport.report_date == today)
        .first()
    )
    if existing is not None:
        topic_count = db.query(PersonalizedTopic).filter(PersonalizedTopic.report_id == existing.id).count()
        if topic_count < 1:
            raise PersonalizedQualityError("今日个性化日报记录不完整，请联系运营者")
        return {"report_id": existing.id, "topics": topic_count, "status": "already_generated"}

    if not has_active_subscription(db, user_id):
        total = db.query(PersonalizedReport).filter(PersonalizedReport.user_id == user_id).count()
        if total >= settings.trial_personalized_reports:
            raise ValueError("体验次数已用完（3 份），请订阅后继续")

    events = (
        db.query(HotEvent)
        .filter(HotEvent.status != EventStatus.archived)
        .order_by(HotEvent.sort_score.desc())
        .limit(15)
        .all()
    )
    event_ids = {event.id for event in events}
    evidence_items = _evidence_items_by_event(db, event_ids)
    events = [
        event
        for event in events
        if not has_unsupported_scale_claim(
            event.title,
            event.summary,
            evidence_items.get(event.id, []),
        )
    ]
    if not events:
        raise ValueError("没有候选热点事件，请稍后再试")

    now = utcnow()
    fresh = [e for e in events if _hours_ago(e.first_seen_at, now) <= settings.topic_fresh_hours]
    if len(fresh) < 3:
        fresh = [e for e in events if _hours_ago(e.first_seen_at, now) <= settings.topic_fresh_relax_hours]
    candidates = fresh[:10] if fresh else events[:10]

    user_prompt = (
        _PROMPT.replace("{profile}", _profile_text(profile))
        .replace("{events}", _events_text(db, candidates))
    )
    if llm.is_available():
        data = llm.complete_json(_PROMPT, user_prompt)
    else:
        if settings.app_env == "prod":
            raise PersonalizedQualityError("个性化日报模型暂不可用，请稍后再试")
        data = _mock(profile, candidates)

    events_by_id = {e.id: e for e in candidates}
    topics_data = _validated_topics(db, data, candidates)

    report = PersonalizedReport(user_id=user_id, report_date=today)
    db.add(report)
    db.flush()

    report.summary = str(data.get("summary") or "")[:1000]
    report.reason = str(data.get("reason") or "")[:2000]

    for idx, t in enumerate(topics_data, start=1):
        event = events_by_id[t["event_id"]]
        reason = str(t.get("publish_reason") or "趁热度最高").strip()
        time_window = f"建议 {_deadline_str(event.first_seen_at)} 前发布，{reason}"
        db.add(
            PersonalizedTopic(
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
                recommendation_reason=str(t.get("recommendation_reason") or ""),
                order_index=idx,
            )
        )

    db.commit()
    return {"report_id": report.id, "topics": len(topics_data), "status": "generated"}
