"""来源条目（SourceItem）：从某信息源采集到的单条原始内容。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .source import Source


class SourceItem(Base):
    __tablename__ = "source_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    # 规范化 URL 的 SHA-256，确定性去重键
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source: Mapped[Source] = relationship("Source")
