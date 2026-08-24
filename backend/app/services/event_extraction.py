"""事件提取编排：来源条目 → 热点事件（含证据、可信度、排序）。"""
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import EventEvidence, HotEvent, Source, SourceItem
from app.models.enums import CredibilityLabel, EventStatus, SourceType
from . import llm
from .credibility import compute_credibility
from .scoring import compute_sort_score

_PROMPT = (Path(__file__).resolve().parent / "prompts" / "event_extraction.md").read_text(encoding="utf-8")
_SUPPLEMENTAL_SOURCE_TYPES = {SourceType.aibase_daily, SourceType.hacker_news}
_MINIMUM_DAILY_CANDIDATES = 3
_UNSUPPORTED_SCALE_RULES = (
    (("辞职潮", "离职潮"), ("辞职潮", "离职潮", "resignation wave", "wave of resignations", "mass resignation", "exodus", "quit in droves")),
    (("大批", "大规模"), ("大批", "大规模", "many", "multiple", "mass ", "large-scale", "large scale")),
    (("集体", "纷纷"), ("集体", "纷纷", "collective", "as a group", "many", "multiple")),
    (("激增", "暴增"), ("激增", "暴增", "surge", "spike", "soar", "jump sharply", "sharp increase")),
)


class EventExtractionQualityError(ValueError):
    """事件提取结果不满足生产内容要求。"""


def select_candidate_items(
    db: Session,
    hours: int = 48,
    limit: int = 150,
    *,
    published_from: datetime | None = None,
    published_before: datetime | None = None,
) -> list[SourceItem]:
    """官方源优先；不足三条时才用补充参考源补位。"""
    since = published_from or (utcnow() - timedelta(hours=hours))
    core_items: list[SourceItem] = []
    supplemental_items: list[SourceItem] = []
    for source in db.query(Source).filter(Source.enabled.is_(True)).all():
        query = db.query(SourceItem).filter(
            SourceItem.source_id == source.id,
            SourceItem.published_at >= since,
        )
        if published_before is not None:
            query = query.filter(SourceItem.published_at < published_before)
        batch = (
            query
            .order_by(SourceItem.published_at.desc())
            .limit(source.max_items_per_day)
            .all()
        )
        target = (
            supplemental_items
            if source.type in _SUPPLEMENTAL_SOURCE_TYPES
            else core_items
        )
        target.extend(batch)

    core_items.sort(key=lambda item: item.published_at, reverse=True)
    if len(core_items) >= _MINIMUM_DAILY_CANDIDATES:
        return core_items[:limit]

    supplemental_items.sort(key=lambda item: item.published_at, reverse=True)
    target_count = min(_MINIMUM_DAILY_CANDIDATES, limit)
    needed = max(0, target_count - len(core_items))
    selected = core_items + supplemental_items[:needed]
    selected.sort(key=lambda x: x.published_at or x.collected_at, reverse=True)
    return selected[:limit]


def _build_items_prompt(items: list[SourceItem]) -> str:
    lines = []
    for it in items:
        ts = it.published_at.strftime("%Y-%m-%d %H:%M") if it.published_at else "未知时间"
        body = (it.body or "").replace("\n", " ")[:300]
        lines.append(
            f"id={it.id} | 来源={it.source.name} | 时间={ts} | 标题={it.title} | 摘要={body}"
        )
    return "\n".join(lines)


def _mock_extract(items: list[SourceItem]) -> dict:
    """无 Key 时的确定性模拟：把前几条两两合并成模拟事件（供界面验收）。"""
    events = []
    for i in range(0, min(20, len(items)), 2):
        first = items[i]
        second = items[i + 1] if i + 1 < len(items) else None
        ids = [first.id] + ([second.id] if second else [])
        events.append(
            {
                "title": f"[模拟] {first.title[:60]}",
                "summary": f"[模拟事件，用于界面验收] {first.title}",
                "evidence_item_ids": ids,
                "relevance_score": 4,
                "actionability_score": 4,
                "reason": "模拟数据；接入真实模型 Key 后由模型生成",
            }
        )
    return {"events": events}


def _freshness(latest: datetime | None) -> int:
    if latest is None:
        return 1
    hours = (utcnow() - latest).total_seconds() / 3600
    if hours < 6:
        return 5
    if hours < 24:
        return 4
    if hours < 48:
        return 3
    if hours < 72:
        return 2
    return 1


def _clamp_score(value) -> int:
    try:
        return max(1, min(5, int(value)))
    except (TypeError, ValueError):
        return 1


def has_unsupported_scale_claim(
    title: object,
    summary: object,
    items: list[SourceItem],
) -> bool:
    """判断标题或摘要是否把原始证据扩大为未经支持的群体现象。"""
    generated = f"{title or ''} {summary or ''}".lower()
    evidence = " ".join(f"{item.title} {item.body or ''}" for item in items).lower()
    return any(
        any(marker in generated for marker in generated_markers)
        and not any(support in evidence for support in evidence_markers)
        for generated_markers, evidence_markers in _UNSUPPORTED_SCALE_RULES
    )


def extract_events(
    db: Session,
    *,
    published_from: datetime | None = None,
    published_before: datetime | None = None,
) -> dict:
    """执行一次事件提取，返回摘要信息。"""
    items = select_candidate_items(
        db,
        published_from=published_from,
        published_before=published_before,
    )
    if not items:
        return {"events_created": 0, "candidates": 0}

    user_prompt = _build_items_prompt(items)
    if llm.is_available():
        data = llm.complete_json(_PROMPT, user_prompt)
    else:
        if settings.app_env == "prod":
            raise EventExtractionQualityError("事件提取模型暂不可用，请稍后再试")
        data = _mock_extract(items)

    valid_ids = {it.id for it in items}
    items_by_id = {it.id: it for it in items}
    # 已归属事件的条目跳过（避免重复证据违反唯一约束）
    assigned_ids = {
        sid for (sid,) in db.query(EventEvidence.source_item_id).all()
    }

    created = 0
    rejected = 0
    for raw in data.get("events", []):
        evidence_ids = [
            int(x) for x in raw.get("evidence_item_ids", []) if str(x).isdigit()
        ]
        evidence_ids = [
            x for x in dict.fromkeys(evidence_ids)
            if x in valid_ids and x not in assigned_ids
        ]
        if not evidence_ids:
            continue

        ev_items = [items_by_id[x] for x in evidence_ids]
        title = str(raw.get("title") or "").strip()
        summary = str(raw.get("summary") or "").strip()
        if not title or not summary or has_unsupported_scale_claim(title, summary, ev_items):
            rejected += 1
            continue
        if settings.app_env == "prod" and "[模拟]" in f"{title} {summary}":
            rejected += 1
            continue
        evidence_sources = [(it.source.id, it.source.credibility_level) for it in ev_items]
        label: CredibilityLabel = compute_credibility(evidence_sources)
        latest_ts = max((it.published_at for it in ev_items if it.published_at), default=None)
        freshness = _freshness(latest_ts)
        relevance = _clamp_score(raw.get("relevance_score"))
        actionability = _clamp_score(raw.get("actionability_score"))

        event = HotEvent(
            title=title[:300],
            summary=summary[:2000],
            credibility_label=label,
            relevance_score=relevance,
            actionability_score=actionability,
            freshness_score=freshness,
            sort_score=compute_sort_score(relevance, actionability, freshness, label),
            reason=(str(raw.get("reason") or "")[:1000] or None),
            status=EventStatus.candidate,
            first_seen_at=latest_ts or utcnow(),
        )
        db.add(event)
        db.flush()
        for sid in evidence_ids:
            db.add(EventEvidence(hot_event_id=event.id, source_item_id=sid))
        created += 1

    db.commit()
    return {"events_created": created, "events_rejected": rejected, "candidates": len(items)}
