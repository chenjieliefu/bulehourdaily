"""可由运营者维护的结构化公开站点内容。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


class SiteContent(Base):
    __tablename__ = "site_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    draft: Mapped[dict] = mapped_column(JSON, nullable=False)
    published: Mapped[dict] = mapped_column(JSON, nullable=False)
    previous_published: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
