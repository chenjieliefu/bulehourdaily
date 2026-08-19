"""发布反馈接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import PersonalizedReport, PersonalizedTopic, TopicFeedback, User
from app.models.enums import FeedbackStatus
from app.schemas.feedback import FeedbackRead, FeedbackUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/topics", tags=["feedback"])


@router.put("/{topic_id}/feedback", response_model=FeedbackRead)
def upsert_feedback(
    topic_id: int,
    payload: FeedbackUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = db.get(PersonalizedTopic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="选题不存在")
    report = db.get(PersonalizedReport, topic.report_id)
    if report is None or report.user_id != user.id:
        raise HTTPException(status_code=404, detail="选题不存在")

    # 已发布状态必须带链接（PRD：已发布可选填，这里不强求；未发布清空链接）
    douyin_url = payload.douyin_url if payload.status == FeedbackStatus.published else None

    feedback = (
        db.query(TopicFeedback)
        .filter(TopicFeedback.user_id == user.id, TopicFeedback.topic_id == topic_id)
        .first()
    )
    if feedback is None:
        feedback = TopicFeedback(user_id=user.id, topic_id=topic_id, status=payload.status, douyin_url=douyin_url)
        db.add(feedback)
    else:
        feedback.status = payload.status
        feedback.douyin_url = douyin_url
    db.commit()
    db.refresh(feedback)
    return feedback
