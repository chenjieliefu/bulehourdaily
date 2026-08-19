"""数据库引擎与会话。SQLite 单文件，MVP 够用。"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# 确保 SQLite 文件目录存在（相对路径时按启动目录解析）
_db_url = settings.database_url
if _db_url.startswith("sqlite:///"):
    _path = _db_url[len("sqlite:///"):]
    if _path and _path != ":memory:":
        _dir = os.path.dirname(_path)
        if _dir:
            os.makedirs(_dir, exist_ok=True)

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False} if _db_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    """FastAPI 依赖：每个请求一个会话，用完关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
