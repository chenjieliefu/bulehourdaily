"""创作者画像（CreatorProfile）：一位创作者一个当前画像。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


class CreatorProfile(Base):
    __tablename__ = "creator_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    positioning: Mapped[str] = mapped_column(Text, nullable=False)   # 账号定位
    audience: Mapped[str] = mapped_column(Text, nullable=False)      # 目标观众
    persona: Mapped[str] = mapped_column(Text, nullable=False)       # 人设
    style: Mapped[str] = mapped_column(Text, nullable=False)         # 表达风格
    video_length: Mapped[str] = mapped_column(Text, nullable=False)  # 常见视频长度
    forbidden: Mapped[str] = mapped_column(Text, nullable=False)     # 内容禁区
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
