"""采集状态接口：最近采集时间、各源状态。"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CollectionRun, Source, SourceItem
from app.models.enums import CollectionStatus
from app.schemas.collect import StatusRead, StatusSource

router = APIRouter(prefix="/status", tags=["status"])


@router.get("", response_model=StatusRead)
def get_status(db: Session = Depends(get_db)):
    last_collect_at = db.query(func.max(CollectionRun.started_at)).scalar()
    total_sources = db.query(func.count(Source.id)).scalar() or 0
    enabled_sources = (
        db.query(func.count(Source.id)).filter(Source.enabled.is_(True)).scalar() or 0
    )
    total_items = db.query(func.count(SourceItem.id)).scalar() or 0

    sources: list[StatusSource] = []
    for s in db.query(Source).order_by(Source.id).all():
        last_run = (
            db.query(CollectionRun)
            .filter(CollectionRun.source_id == s.id)
            .order_by(CollectionRun.id.desc())
            .first()
        )
        last_success = (
            db.query(CollectionRun)
            .filter(
                CollectionRun.source_id == s.id,
                CollectionRun.status == CollectionStatus.success,
            )
            .order_by(CollectionRun.id.desc())
            .first()
        )
        sources.append(
            StatusSource(
                source_id=s.id,
                source_name=s.name,
                type=s.type,
                credibility_level=s.credibility_level,
                max_items_per_day=s.max_items_per_day,
                enabled=s.enabled,
                last_success_at=last_success.finished_at if last_success else None,
                last_status=last_run.status if last_run else None,
                last_error=last_run.error_message if last_run else None,
            )
        )

    return StatusRead(
        last_collect_at=last_collect_at,
        total_sources=total_sources,
        enabled_sources=enabled_sources,
        total_items=total_items,
        sources=sources,
    )
