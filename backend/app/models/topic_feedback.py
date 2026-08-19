"""发布反馈（TopicFeedback）：创作者对个性化选题的反馈。"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from .enums import FeedbackStatus


class TopicFeedback(Base):
    __tablename__ = "topic_feedback"
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="uq_feedback_user_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("personalized_topic.id"), nullable=False
    )
    status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus, name="feedback_status"), nullable=False
    )
    douyin_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
