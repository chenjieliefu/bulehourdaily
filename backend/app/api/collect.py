"""采集接口：手动触发一次全量采集。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.collect import CollectRunSummary
from app.services.auth import get_current_operator
from app.services.collection import collect_all

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post(
    "/run",
    response_model=CollectRunSummary,
    dependencies=[Depends(get_current_operator)],
)
def run_collection(db: Session = Depends(get_db)):
    return collect_all(db)
