"""邮件送达记录（MailDelivery）：MVP 本地模拟发送，记录内容与状态。"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from .enums import MailStatus


class MailDelivery(Base):
    __tablename__ = "mail_delivery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    report_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("personalized_report.id"), nullable=True
    )
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MailStatus] = mapped_column(
        Enum(MailStatus, name="mail_status"), default=MailStatus.pending, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
