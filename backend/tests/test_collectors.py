"""采集器解析纯函数测试。"""
from datetime import datetime

from app.services.collectors import _entry_to_item, _parse_time


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
