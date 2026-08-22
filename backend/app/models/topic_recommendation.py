"""选题建议（TopicRecommendation）：日报中的三个主选题。"""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TopicRecommendation(Base):
    __tablename__ = "topic_recommendation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("daily_report.id"), nullable=False, index=True
    )
    hot_event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hot_event.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    what_happened: Mapped[str] = mapped_column(Text, nullable=False)
    why_now: Mapped[str] = mapped_column(Text, nullable=False)
    angle: Mapped[str] = mapped_column(Text, nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    structure: Mapped[str] = mapped_column(Text, nullable=False)
    visual: Mapped[str] = mapped_column(Text, nullable=False)
    time_window: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
