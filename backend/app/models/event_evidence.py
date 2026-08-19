"""事件证据（EventEvidence）：热点事件与来源条目的关联。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from .hot_event import HotEvent
from .source_item import SourceItem


class EventEvidence(Base):
    __tablename__ = "event_evidence"
    __table_args__ = (
        UniqueConstraint("source_item_id", name="uq_event_evidence_source_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hot_event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hot_event.id"), nullable=False, index=True
    )
    source_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source_item.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    hot_event: Mapped[HotEvent] = relationship("HotEvent", backref="evidence")
    source_item: Mapped[SourceItem] = relationship("SourceItem")
