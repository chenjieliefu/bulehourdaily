"""采集器：从信息源抓取条目。

- rss / github_releases：HTTP + feedparser 解析。
- x：本阶段占位，返回空（真实 X 采集商业上线前接入）。
"""
import calendar
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from app.core.config import settings
from app.models.enums import SourceType


def _parse_time(struct: Any) -> datetime | None:
    """feedparser 的 *_parsed 是 UTC struct_time。"""
    if not struct:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(struct), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _entry_to_item(entry: Any) -> dict | None:
    """把 feedparser 条目转成统一结构；无有效链接的条目丢弃。"""
    link = entry.get("link") or entry.get("id") or ""
    title = (entry.get("title") or "").strip()
    if not link.startswith(("http://", "https://")):
        return None
    if not title:
        return None

    published = _parse_time(entry.get("published_parsed") or entry.get("updated_parsed"))
    body = (entry.get("summary") or entry.get("description") or "").strip()
    author = (entry.get("author") or "").strip()

    # 只存可 JSON 序列化的原始片段，避免 feedparser 内部对象
    raw = {
        "title": title[:500],
        "link": link,
        "summary": body[:2000],
        "published": published.isoformat() if published else None,
    }
    return {
        "title": title[:500],
        "body": body or None,
        "author": author or None,
        "url": link,
        "published_at": published,
        "raw": raw,
    }


def fetch_items(source_type: SourceType, url: str) -> list[dict]:
    """抓取并解析一个信息源，返回条目列表。异常向上抛，由编排层记录失败。"""
    if source_type == SourceType.x:
        # 占位：真实 X 采集后续接入（见决策备忘）
        return []

    response = httpx.get(
        url,
        timeout=settings.collect_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": "weilan-daily/0.1 (+local MVP collector)"},
    )
    response.raise_for_status()

    parsed = feedparser.parse(response.content)
    items: list[dict] = []
    for entry in parsed.entries:
        item = _entry_to_item(entry)
        if item:
            items.append(item)
    return items
