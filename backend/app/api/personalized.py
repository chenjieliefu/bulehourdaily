"""个性化日报接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    EventEvidence,
    HotEvent,
    PersonalizedReport,
    PersonalizedTopic,
    SourceItem,
    User,
)
from app.models.enums import JobKind
from app.schemas.event import EvidenceItem
from app.schemas.personalized import (
    PersonalizedReportDetail,
    PersonalizedReportRead,
    PersonalizedTopicRead,
)
from app.services.auth import get_current_user
from app.services.jobs import run_in_background

router = APIRouter(prefix="/personalized", tags=["personalized"])


def _evidence_for_events(db: Session, event_ids: list[int]) -> dict[int, list[EvidenceItem]]:
    if not event_ids:
        return {}
    evs = db.query(EventEvidence).filter(EventEvidence.hot_event_id.in_(event_ids)).all()
    items = {i.id: i for i in db.query(SourceItem).filter(SourceItem.id.in_([e.source_item_id for e in evs])).all()}
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


@router.post("/generate", status_code=202)
def trigger_generate(user: User = Depends(get_current_user)):
    job_id = run_in_background(JobKind.personalized_report, context={"user_id": user.id})
    return {"job_id": job_id}


@router.get("/reports", response_model=list[PersonalizedReportRead])
def list_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(PersonalizedReport)
        .filter(PersonalizedReport.user_id == user.id)
        .order_by(PersonalizedReport.report_date.desc())
        .all()
    )


@router.get("/reports/{report_id}", response_model=PersonalizedReportDetail)
def get_report(report_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.get(PersonalizedReport, report_id)
    if report is None or report.user_id != user.id:
        raise HTTPException(status_code=404, detail="not found")

    topics = (
        db.query(PersonalizedTopic)
        .filter(PersonalizedTopic.report_id == report_id)
        .order_by(PersonalizedTopic.order_index)
        .all()
    )
    event_ids = [t.hot_event_id for t in topics]
    events = {e.id: e for e in db.query(HotEvent).filter(HotEvent.id.in_(event_ids)).all()} if event_ids else {}
    evidence_map = _evidence_for_events(db, event_ids)

    topic_reads = [
        PersonalizedTopicRead(
            id=t.id,
            title=t.title,
            what_happened=t.what_happened,
            why_now=t.why_now,
            angle=t.angle,
            hook=t.hook,
            structure=t.structure,
            visual=t.visual,
            time_window=t.time_window,
            recommendation_reason=t.recommendation_reason,
            order_index=t.order_index,
            hot_event_id=t.hot_event_id,
            credibility_label=events[t.hot_event_id].credibility_label if t.hot_event_id in events else None,
            event_published_at=events[t.hot_event_id].first_seen_at if t.hot_event_id in events else None,
            evidence=evidence_map.get(t.hot_event_id, []),
        )
        for t in topics
    ]

    base = PersonalizedReportRead.model_validate(report)
    return PersonalizedReportDetail(**base.model_dump(), topics=topic_reads)
