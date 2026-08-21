"""热点事件接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import EventEvidence, HotEvent, SourceItem
from app.models.enums import JobKind
from app.schemas.event import EventDetail, EventRead, EvidenceItem
from app.services.auth import get_current_operator
from app.services.jobs import run_in_background

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "/extract",
    status_code=202,
    dependencies=[Depends(get_current_operator)],
)
def trigger_extract():
    job_id = run_in_background(JobKind.extract_events)
    return {"job_id": job_id}


def _read(e: HotEvent, evidence_count: int) -> EventRead:
    return EventRead(
        id=e.id,
        title=e.title,
        summary=e.summary,
        credibility_label=e.credibility_label,
        relevance_score=e.relevance_score,
        actionability_score=e.actionability_score,
        freshness_score=e.freshness_score,
        sort_score=e.sort_score,
        reason=e.reason,
        status=e.status,
        first_seen_at=e.first_seen_at,
        evidence_count=evidence_count,
    )


@router.get("", response_model=list[EventRead])
def list_events(db: Session = Depends(get_db)):
    events = db.query(HotEvent).order_by(HotEvent.sort_score.desc()).all()
    counts = dict(
        db.query(EventEvidence.hot_event_id, func.count(EventEvidence.id))
        .group_by(EventEvidence.hot_event_id)
        .all()
    )
    return [_read(e, counts.get(e.id, 0)) for e in events]


@router.get("/{event_id}", response_model=EventDetail)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(HotEvent, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")

    evidence: list[EvidenceItem] = []
    for ev in (
        db.query(EventEvidence).filter(EventEvidence.hot_event_id == event_id).all()
    ):
        item = db.get(SourceItem, ev.source_item_id)
        if item is None:
            continue
        evidence.append(
            EvidenceItem(
                source_item_id=item.id,
                title=item.title,
                url=item.url,
                source_name=item.source.name,
                published_at=item.published_at,
            )
        )

    base = _read(event, len(evidence))
    return EventDetail(**base.model_dump(), evidence=evidence)
