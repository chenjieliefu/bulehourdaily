"""统一时间处理：数据库统一存「无时区的 UTC」，前端展示时再加时区。"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """返回无时区的 UTC 当前时间（存储用）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)
