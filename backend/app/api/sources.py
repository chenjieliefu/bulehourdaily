"""信息源接口。读取公开，写操作仅限运营者。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Source
from app.schemas.source import SourceCreate, SourceRead, SourceUpdate
from app.services.auth import get_current_operator

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
def list_sources(
    enabled: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Source)
    if enabled is not None:
        q = q.filter(Source.enabled.is_(enabled))
    return q.order_by(Source.id).all()


@router.post("", response_model=SourceRead, status_code=201, dependencies=[Depends(get_current_operator)])
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceRead, dependencies=[Depends(get_current_operator)])
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204, dependencies=[Depends(get_current_operator)])
def disable_source(source_id: int, db: Session = Depends(get_db)):
    """软停用，不物理删除（保留历史条目关联）。"""
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    source.enabled = False
    db.commit()
