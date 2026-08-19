"""热点事件（HotEvent）：由多个来源条目共同描述的同一件事。"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from .enums import CredibilityLabel, EventStatus


class HotEvent(Base):
    __tablename__ = "hot_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    credibility_label: Mapped[CredibilityLabel] = mapped_column(
        Enum(CredibilityLabel, name="credibility_label"), nullable=False
    )
    relevance_score: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    actionability_score: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    freshness_score: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        default=EventStatus.candidate,
        nullable=False,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
