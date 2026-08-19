"""通用日报（DailyReport）：每天一份的主日报。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .enums import ReportStatus


class DailyReport(Base):
    __tablename__ = "daily_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"),
        default=ReportStatus.draft,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
