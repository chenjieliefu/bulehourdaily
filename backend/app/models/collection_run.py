"""采集运行记录（CollectionRun）：可追踪到具体信息源与失败时间。"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .enums import CollectionStatus
from .source import Source


class CollectionRun(Base):
    __tablename__ = "collection_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[CollectionStatus] = mapped_column(
        Enum(CollectionStatus, name="collection_status"),
        default=CollectionStatus.running,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    source: Mapped[Source] = relationship("Source")
