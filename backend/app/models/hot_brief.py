"""热点速览（HotBrief）：日报中未进入主选题的简短摘要。"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HotBrief(Base):
    __tablename__ = "hot_brief"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("daily_report.id"), nullable=False, index=True
    )
    hot_event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hot_event.id"), nullable=False
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
