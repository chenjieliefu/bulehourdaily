"""来源条目接口。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SourceItem
from app.schemas.source_item import SourceItemRead

router = APIRouter(prefix="/source-items", tags=["source-items"])


@router.get("", response_model=list[SourceItemRead])
def list_source_items(
    source_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(SourceItem)
    if source_id is not None:
        q = q.filter(SourceItem.source_id == source_id)
    return q.order_by(SourceItem.collected_at.desc()).offset(offset).limit(limit).all()
