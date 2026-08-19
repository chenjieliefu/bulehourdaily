"""个性化日报（PersonalizedReport）：每位创作者每天的个性化日报。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


class PersonalizedReport(Base):
    __tablename__ = "personalized_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # 为什么今天推荐给你
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
