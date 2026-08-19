"""个性化选题（PersonalizedTopic）：仍引用共享热点事件，只改选择与表达角度。"""
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PersonalizedTopic(Base):
    __tablename__ = "personalized_topic"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("personalized_report.id"), nullable=False, index=True
    )
    hot_event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hot_event.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    what_happened: Mapped[str] = mapped_column(Text, nullable=False)
    why_now: Mapped[str] = mapped_column(Text, nullable=False)
    angle: Mapped[str] = mapped_column(Text, nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    structure: Mapped[str] = mapped_column(Text, nullable=False)
    visual: Mapped[str] = mapped_column(Text, nullable=False)
    time_window: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_reason: Mapped[str] = mapped_column(Text, nullable=False)  # 为什么适合这个账号
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
