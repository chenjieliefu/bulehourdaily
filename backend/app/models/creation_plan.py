"""创作方案（CreationPlan）：展开个性化选题后的可拍摄执行方案。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


class CreationPlan(Base):
    __tablename__ = "creation_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("personalized_topic.id"), nullable=False, unique=True
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    core_viewpoint: Mapped[str] = mapped_column(Text, nullable=False)   # 核心观点
    hooks: Mapped[list | None] = mapped_column(JSON, nullable=True)     # 2-3 个开场钩子
    structure: Mapped[str] = mapped_column(Text, nullable=False)        # 60-90 秒结构
    visual: Mapped[str] = mapped_column(Text, nullable=False)           # 画面建议
    titles: Mapped[list | None] = mapped_column(JSON, nullable=True)    # 标题方向
    risks: Mapped[str] = mapped_column(Text, nullable=False)            # 风险提示
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
