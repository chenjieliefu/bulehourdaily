"""测试公共夹具：内存 SQLite + 数据工厂。"""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.models import Source, SourceItem
from app.models.enums import CredibilityLevel, SourceType
from app.services.url_normalize import url_hash


@pytest.fixture(autouse=True)
def _force_mock_llm(monkeypatch):
    """测试一律走 mock，不调用真实模型（真实冒烟另做）。"""
    monkeypatch.setattr(settings, "model_api_key", "")


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def source_factory(db):
    def _f(name="src", type_=SourceType.rss, level=CredibilityLevel.official, max_per_day=5, url=None):
        s = Source(
            name=name,
            type=type_,
            url=url or f"https://example.com/{name}",
            enabled=True,
            credibility_level=level,
            max_items_per_day=max_per_day,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    return _f


@pytest.fixture()
def item_factory(db):
    def _f(source, title="item", url=None):
        url = url or f"https://example.com/{source.id}/{title}"
        it = SourceItem(
            source_id=source.id,
            title=title,
            url=url,
            url_hash=url_hash(url),
            collected_at=datetime.utcnow(),
        )
        db.add(it)
        db.commit()
        db.refresh(it)
        return it

    return _f
