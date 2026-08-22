"""采集器解析纯函数测试。"""
from datetime import datetime, timezone

import pytest

from app.models.enums import SourceType
from app.services.collectors import (
    _entry_to_item,
    _hn_item_to_item,
    _parse_aibase_daily,
    _parse_aibase_latest_url,
    _parse_time,
    fetch_items,
)


def test_entry_to_item_basic():
    entry = {
        "link": "https://example.com/post",
        "title": "Hello AI",
        "summary": "Some summary",
        "author": "Alice",
        "published_parsed": (2026, 8, 1, 0, 0, 0, 0, 0, 0),
    }
    item = _entry_to_item(entry)
    assert item is not None
    assert item["url"] == "https://example.com/post"
    assert item["title"] == "Hello AI"
    assert item["author"] == "Alice"
    assert item["published_at"] == datetime(2026, 8, 1)
    assert item["raw"]["link"] == "https://example.com/post"


def test_entry_without_link_skipped():
    assert _entry_to_item({"title": "no link"}) is None


def test_entry_without_title_skipped():
    assert _entry_to_item({"link": "https://example.com/x"}) is None


def test_entry_falls_back_to_id():
    entry = {"id": "https://example.com/by-id", "title": "By ID"}
    item = _entry_to_item(entry)
    assert item is not None
    assert item["url"] == "https://example.com/by-id"


def test_parse_time_none():
    assert _parse_time(None) is None


def test_observation_page_is_not_reported_as_successful_collection():
    with pytest.raises(ValueError, match="观察源"):
        fetch_items(SourceType.web_page, "https://example.com/updates")


def test_aibase_uses_only_latest_daily_link():
    html = """
    <a href="/zh/daily/30532">今天的日报</a>
    <a href="/zh/daily/30505">昨天的日报</a>
    """

    assert _parse_aibase_latest_url(html, "https://news.aibase.com/zh/daily") == (
        "https://news.aibase.com/zh/daily/30532"
    )


def test_aibase_keeps_at_most_two_items_with_original_links():
    html = """
    <script>
      {"content":"2、脚本中的假消息 详情链接:https://bad.example/\u003Cp\u003E"}
    </script>
    <article>
      <div>发布时间 : 2026年8月22号 08:00</div>
      <h2>1、OpenAI 发布新功能</h2>
      <p>这是一段不应被复制入库的聚合摘要。</p>
      <p>详情链接: <a href="https://openai.com/news/example">https://openai.com/news/example</a></p>
      <h2>2、没有原文链接的消息</h2>
      <p>只有聚合站自己的描述。</p>
      <h2>3、Runway 发布创作工具</h2>
      <p>另一段不应被复制入库的聚合摘要。</p>
      <p>详情链接: <a href="https://runwayml.com/news/example">https://runwayml.com/news/example</a></p>
      <h2>4、第三条带链接的消息</h2>
      <p>详情链接: <a href="https://example.org/third">https://example.org/third</a></p>
    </article>
    """

    items = _parse_aibase_daily(
        html,
        "https://news.aibase.com/zh/daily/30532",
        now=datetime(2026, 8, 22, 1, 0),
    )

    assert [item["title"] for item in items] == [
        "OpenAI 发布新功能",
        "Runway 发布创作工具",
    ]
    assert [item["url"] for item in items] == [
        "https://openai.com/news/example",
        "https://runwayml.com/news/example",
    ]
    assert all(item["body"] is None for item in items)
    assert all(item["raw"]["source_kind"] == "aggregated_reference" for item in items)


def test_aibase_rejects_stale_daily():
    html = """
    <article>
      <div>发布时间 : 2026年8月19号 08:00</div>
      <h2>1、旧消息</h2>
      <p>详情链接: <a href="https://example.com/old">https://example.com/old</a></p>
    </article>
    """

    assert _parse_aibase_daily(
        html,
        "https://news.aibase.com/zh/daily/old",
        now=datetime(2026, 8, 22, 1, 0),
    ) == []


def test_hacker_news_accepts_recent_ai_story_with_engagement():
    now = datetime(2026, 8, 22, 12, 0)
    raw = {
        "id": 123,
        "type": "story",
        "title": "OpenAI releases a new image generation model",
        "url": "https://openai.com/news/image-model",
        "by": "alice",
        "score": 5,
        "descendants": 1,
        "time": int(datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc).timestamp()),
    }

    item = _hn_item_to_item(raw, now=now)

    assert item is not None
    assert item["url"] == "https://openai.com/news/image-model"
    assert item["published_at"] == datetime(2026, 8, 22, 10, 0)
    assert item["raw"]["source_kind"] == "community_signal"


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "PostgreSQL indexing internals"},
        {"score": 4, "descendants": 2},
        {"time": int(datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc).timestamp())},
        {"url": ""},
    ],
)
def test_hacker_news_rejects_irrelevant_low_signal_old_or_linkless_story(changes):
    raw = {
        "id": 123,
        "type": "story",
        "title": "OpenAI releases a new model",
        "url": "https://openai.com/news/model",
        "by": "alice",
        "score": 5,
        "descendants": 1,
        "time": int(datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc).timestamp()),
    }
    raw.update(changes)

    assert _hn_item_to_item(raw, now=datetime(2026, 8, 22, 12, 0)) is None
