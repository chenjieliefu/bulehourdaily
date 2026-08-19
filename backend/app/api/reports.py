"""通用日报接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    CollectionRun,
    DailyReport,
    EventEvidence,
    HotBrief,
    HotEvent,
    SourceItem,
    TopicRecommendation,
)
from app.models.enums import JobKind
from app.schemas.event import EvidenceItem
from app.schemas.report import BriefRead, ReportDetail, ReportRead, TopicRead
from app.services.jobs import run_in_background

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", status_code=202)
def trigger_generate():
    job_id = run_in_background(JobKind.generate_report)
    return {"job_id": job_id}


@router.get("", response_model=list[ReportRead])
def list_reports(db: Session = Depends(get_db)):
    return db.query(DailyReport).order_by(DailyReport.report_date.desc()).all()


def _evidence_for_events(db: Session, event_ids: list[int]) -> dict[int, list[EvidenceItem]]:
    if not event_ids:
        return {}
    evs = (
        db.query(EventEvidence).filter(EventEvidence.hot_event_id.in_(event_ids)).all()
    )
    item_ids = [ev.source_item_id for ev in evs]
    items = {i.id: i for i in db.query(SourceItem).filter(SourceItem.id.in_(item_ids)).all()}
    result: dict[int, list[EvidenceItem]] = {}
    for ev in evs:
        item = items.get(ev.source_item_id)
        if item is None:
            continue
        result.setdefault(ev.hot_event_id, []).append(
            EvidenceItem(
                source_item_id=item.id,
                title=item.title,
                url=item.url,
                source_name=item.source.name,
                published_at=item.published_at,
            )
        )
    return result


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(DailyReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")

    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report_id)
        .order_by(TopicRecommendation.order_index)
        .all()
    )
    briefs = (
        db.query(HotBrief)
        .filter(HotBrief.report_id == report_id)
        .order_by(HotBrief.order_index)
        .all()
    )

    event_ids = list({t.hot_event_id for t in topics} | {b.hot_event_id for b in briefs})
    events = {e.id: e for e in db.query(HotEvent).filter(HotEvent.id.in_(event_ids)).all()} if event_ids else {}
    evidence_map = _evidence_for_events(db, event_ids)
    last_collect_at = db.query(func.max(CollectionRun.started_at)).scalar()

    topic_reads = [
        TopicRead(
            id=t.id,
            title=t.title,
            what_happened=t.what_happened,
            why_now=t.why_now,
            angle=t.angle,
            hook=t.hook,
            structure=t.structure,
            visual=t.visual,
            time_window=t.time_window,
            order_index=t.order_index,
            hot_event_id=t.hot_event_id,
            credibility_label=events[t.hot_event_id].credibility_label if t.hot_event_id in events else None,
            event_published_at=events[t.hot_event_id].first_seen_at if t.hot_event_id in events else None,
            evidence=evidence_map.get(t.hot_event_id, []),
        )
        for t in topics
    ]
    brief_reads = [
        BriefRead(
            id=b.id,
            summary=b.summary,
            order_index=b.order_index,
            hot_event_id=b.hot_event_id,
            event_published_at=events[b.hot_event_id].first_seen_at if b.hot_event_id in events else None,
            evidence=evidence_map.get(b.hot_event_id, []),
        )
        for b in briefs
    ]

    base = ReportRead.model_validate(report)
    return ReportDetail(
        **base.model_dump(),
        last_collect_at=last_collect_at,
        topics=topic_reads,
        briefs=brief_reads,
    )
