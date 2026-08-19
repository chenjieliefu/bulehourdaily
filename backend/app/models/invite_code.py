"""邀请码（InviteCode）：邀请制注册，一次性使用。"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InviteCode(Base):
    __tablename__ = "invite_code"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
