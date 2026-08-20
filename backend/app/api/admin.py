"""轻量质检与邀请码接口（运营者，本地直调）。"""
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import DailyReport, EventEvidence, HotEvent, InviteCode, SourceItem, TopicRecommendation
from app.schemas.admin import (
    AddTopicRequest,
    CandidateEvent,
    InviteCodeCreate,
    InviteCodeRead,
    ReviewPayload,
    ReviewTopic,
    TopicEdit,
)
from app.schemas.event import EvidenceItem
from app.services import admin as admin_svc
from app.services.auth import require_operator

_BJ = ZoneInfo("Asia/Shanghai")
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_operator)])


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
            EvidenceItem(source_item_id=item.id, title=item.title, url=item.url,
                         source_name=item.source.name, published_at=item.published_at)
        )
    return result


@router.get("/review", response_model=ReviewPayload)
def review(db: Session = Depends(get_db)):
    today = datetime.now(_BJ).date()
    report = db.query(DailyReport).filter(DailyReport.report_date == today).first()
    topics: list[TopicRecommendation] = []
    if report:
        topics = (
            db.query(TopicRecommendation)
            .filter(TopicRecommendation.report_id == report.id)
            .order_by(TopicRecommendation.order_index)
            .all()
        )

    event_ids = [t.hot_event_id for t in topics]
    events = {e.id: e for e in db.query(HotEvent).filter(HotEvent.id.in_(event_ids)).all()} if event_ids else {}
    evidence_map = _evidence_for_events(db, event_ids)

    topic_reads = [
        ReviewTopic(
            id=t.id, title=t.title, what_happened=t.what_happened, why_now=t.why_now,
            angle=t.angle, hook=t.hook, structure=t.structure, visual=t.visual,
            time_window=t.time_window, order_index=t.order_index, hot_event_id=t.hot_event_id,
            credibility_label=events[t.hot_event_id].credibility_label if t.hot_event_id in events else None,
            reviewed=t.reviewed,
            evidence=evidence_map.get(t.hot_event_id, []),
        )
        for t in topics
    ]

    candidates = admin_svc.candidate_events(db, set(event_ids))
    candidate_reads = [
        CandidateEvent(
            id=e.id, title=e.title, summary=e.summary,
            credibility_label=e.credibility_label, sort_score=e.sort_score,
            evidence_count=len(evidence_map.get(e.id, [])) or db.query(EventEvidence).filter(EventEvidence.hot_event_id == e.id).count(),
        )
        for e in candidates
    ]

    return ReviewPayload(
        report_id=report.id if report else None,
        report_date=report.report_date if report else None,
        status=report.status if report else None,
        summary=report.summary if report else None,
        published_at=report.published_at if report else None,
        topics=topic_reads,
        candidates=candidate_reads,
    )


@router.put("/topics/{topic_id}", response_model=ReviewTopic)
def edit_topic(topic_id: int, payload: TopicEdit, db: Session = Depends(get_db)):
    try:
        admin_svc.edit_topic(db, topic_id, payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _topic_read(db, topic_id)


@router.post("/topics/{topic_id}/approve")
def approve_topic(topic_id: int, db: Session = Depends(get_db)):
    try:
        admin_svc.approve_topic(db, topic_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ok": True}


@router.delete("/topics/{topic_id}", status_code=204)
def reject_topic(topic_id: int, db: Session = Depends(get_db)):
    try:
        admin_svc.reject_topic(db, topic_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/topics")
def add_topic(payload: AddTopicRequest, db: Session = Depends(get_db)):
    try:
        admin_svc.add_topic_from_event(db, payload.event_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/report/publish")
def publish(db: Session = Depends(get_db)):
    try:
        admin_svc.publish_report(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/invite-codes", response_model=list[InviteCodeRead])
def create_invite_codes(payload: InviteCodeCreate, db: Session = Depends(get_db)):
    codes = []
    for _ in range(payload.count):
        while True:
            code = "WL" + secrets.token_hex(4).upper()
            if db.query(InviteCode).filter(InviteCode.code == code).first() is None:
                break
        row = InviteCode(code=code)
        db.add(row)
        codes.append(row)
    db.commit()
    for c in codes:
        db.refresh(c)
    return codes


@router.get("/invite-codes", response_model=list[InviteCodeRead])
def list_invite_codes(db: Session = Depends(get_db)):
    return db.query(InviteCode).order_by(InviteCode.id.desc()).limit(100).all()


def _topic_read(db: Session, topic_id: int) -> ReviewTopic:
    t = db.get(TopicRecommendation, topic_id)
    if t is None:
        raise HTTPException(status_code=404, detail="选题不存在")
    event = db.get(HotEvent, t.hot_event_id)
    evidence = _evidence_for_events(db, [t.hot_event_id]).get(t.hot_event_id, [])
    return ReviewTopic(
        id=t.id, title=t.title, what_happened=t.what_happened, why_now=t.why_now,
        angle=t.angle, hook=t.hook, structure=t.structure, visual=t.visual,
        time_window=t.time_window, order_index=t.order_index, hot_event_id=t.hot_event_id,
        credibility_label=event.credibility_label if event else None,
        reviewed=t.reviewed, evidence=evidence,
    )
