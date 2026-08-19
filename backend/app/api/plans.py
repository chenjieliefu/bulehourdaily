"""创作方案接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CreationPlan, PersonalizedReport, PersonalizedTopic, User
from app.models.enums import JobKind
from app.schemas.plan import PlanRead
from app.services.auth import get_current_user
from app.services.jobs import run_in_background

router = APIRouter(prefix="/topics", tags=["plans"])


def _owned_topic(db: Session, user_id: int, topic_id: int) -> PersonalizedTopic:
    topic = db.get(PersonalizedTopic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="选题不存在")
    report = db.get(PersonalizedReport, topic.report_id)
    if report is None or report.user_id != user_id:
        raise HTTPException(status_code=404, detail="选题不存在")
    return topic


@router.post("/{topic_id}/plan", status_code=202)
def trigger_plan(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_topic(db, user.id, topic_id)
    job_id = run_in_background(JobKind.generate_plan, context={"user_id": user.id, "topic_id": topic_id})
    return {"job_id": job_id}


@router.get("/{topic_id}/plan", response_model=PlanRead)
def get_plan(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_topic(db, user.id, topic_id)
    plan = db.query(CreationPlan).filter(CreationPlan.topic_id == topic_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="还没有创作方案，请先生成")
    return plan
