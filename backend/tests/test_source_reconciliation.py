"""来源名单同步：保留历史记录，只停用旧来源并启用已确认名单。"""
from app.models import Source, SourceItem
from app.models.enums import CredibilityLevel, SourceType
from app.services.source_reconciliation import reconcile_sources
from app.services.url_normalize import url_hash


def test_reconcile_sources_preserves_history_and_is_idempotent(db):
    openai = Source(
        name="OpenAI News",
        type=SourceType.rss,
        url="https://openai.com/old-feed.xml",
        enabled=True,
        credibility_level=CredibilityLevel.official,
        max_items_per_day=9,
    )
    old_hn = Source(
        name="Hacker News",
        type=SourceType.rss,
        url="https://news.ycombinator.com/rss",
        enabled=True,
        credibility_level=CredibilityLevel.media,
        max_items_per_day=3,
    )
    old_x = Source(
        name="X: example",
        type=SourceType.x,
        url="https://x.com/example",
        enabled=True,
        credibility_level=CredibilityLevel.official,
        max_items_per_day=2,
    )
    db.add_all([openai, old_hn, old_x])
    db.commit()
    db.refresh(openai)
    db.refresh(old_hn)
    db.refresh(old_x)
    historical_item = SourceItem(
        source_id=old_hn.id,
        title="历史 HN 内容",
        url="https://example.com/historical-hn",
        url_hash=url_hash("https://example.com/historical-hn"),
    )
    db.add(historical_item)
    db.commit()

    first = reconcile_sources(db)

    assert first["desired"] == 13
    assert db.get(Source, openai.id).enabled is True
    assert db.get(Source, openai.id).url == "https://openai.com/news/rss.xml"
    assert db.get(Source, old_hn.id).enabled is False
    assert db.get(Source, old_x.id).enabled is False
    assert db.query(SourceItem).filter_by(title="历史 HN 内容").one().source_id == old_hn.id

    enabled_names = {
        source.name for source in db.query(Source).filter(Source.enabled.is_(True)).all()
    }
    assert enabled_names == {
        "OpenAI News",
        "Google AI Blog",
        "Google DeepMind Blog",
        "Midjourney Updates",
        "AIBase 最新 AI 日报",
        "Hacker News AI 线索",
    }
    assert db.query(Source).filter(Source.name == "Hacker News").one().enabled is False
    assert db.query(Source).filter(Source.name == "Hacker News AI 线索").one().enabled is True

    count_after_first = db.query(Source).count()
    second = reconcile_sources(db)

    assert second["created"] == 0
    assert db.query(Source).count() == count_after_first
