"""采集器：从信息源抓取条目。

- rss / github_releases：HTTP + feedparser 解析。
- x：本阶段占位，返回空（真实 X 采集商业上线前接入）。
- web_page：官网观察源，页面采集接入前拒绝自动执行。
- aibase_daily：只读取最新一期日报中带原文链接的前两条线索。
- hacker_news：使用官方 API，筛选最近 24 小时的 AI 社区线索。
"""
import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import re
from typing import Any
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

import feedparser
import httpx

from app.core.config import settings
from app.core.time import utcnow
from app.models.enums import SourceType


_HEADERS = {"User-Agent": "weilan-daily/0.1 (+local MVP collector)"}
_AIBASE_DAILY_LIMIT = 2
_HN_SCAN_LIMIT = 50
_HN_RESULT_LIMIT = 3
_HN_AI_PATTERN = re.compile(
    r"(?:\bartificial intelligence\b|\bmachine learning\b|\blarge language models?\b|"
    r"\bAI\b|\bLLMs?\b|\bOpenAI\b|\bAnthropic\b|\bClaude\b|\bChatGPT\b|"
    r"\bGPT(?:-?\d[\w.-]*)?\b|\bGemini\b|\bDeepMind\b|\bDeepSeek\b|"
    r"\bQwen\b|\bKimi\b|\bMiniMax\b|\bMidjourney\b|\bRunway\b|"
    r"\bdiffusion model\b|\bimage generation\b|\bvideo generation\b|"
    r"\bAI agents?\b|\bagentic\b|\bmultimodal\b|\btransformer models?\b)",
    re.IGNORECASE,
)


class _TextAndLinksParser(HTMLParser):
    """轻量提取网页文本和链接，避免为了两个固定页面引入整套爬虫依赖。"""

    _BLOCK_TAGS = {
        "article", "br", "div", "h1", "h2", "h3", "h4", "li", "p", "section",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in self._BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if self._ignored_depth:
            return
        if tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        self.parts.append(data)

    @property
    def text(self) -> str:
        return "".join(self.parts)


def _request_text(url: str) -> str:
    response = httpx.get(
        url,
        timeout=settings.collect_timeout_seconds,
        follow_redirects=True,
        headers=_HEADERS,
    )
    response.raise_for_status()
    return response.text


def _request_json(url: str) -> Any:
    response = httpx.get(
        url,
        timeout=settings.collect_timeout_seconds,
        follow_redirects=True,
        headers=_HEADERS,
    )
    response.raise_for_status()
    return response.json()


def _parse_time(struct: Any) -> datetime | None:
    """feedparser 的 *_parsed 是 UTC struct_time。"""
    if not struct:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(struct), tz=timezone.utc).replace(tzinfo=None)
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


def _parse_aibase_latest_url(html: str, list_url: str) -> str | None:
    parser = _TextAndLinksParser()
    parser.feed(html)
    for href in parser.links:
        candidate = urljoin(list_url, href)
        parts = urlsplit(candidate)
        if parts.hostname == "news.aibase.com" and re.fullmatch(r"/zh/daily/\d+", parts.path):
            return candidate
    return None


def _parse_aibase_daily(
    html: str,
    page_url: str,
    *,
    now: datetime | None = None,
) -> list[dict]:
    """只保留最新日报中带外部原文的前两条，不复制聚合站摘要。"""
    parser = _TextAndLinksParser()
    parser.feed(html)
    text = parser.text
    published_match = re.search(
        r"发布时间\s*[:：]\s*(\d{4})年(\d{1,2})月(\d{1,2})号\s*(\d{1,2}):(\d{2})",
        text,
    )
    if not published_match:
        return []

    year, month, day, hour, minute = map(int, published_match.groups())
    published_local = datetime(
        year, month, day, hour, minute, tzinfo=ZoneInfo("Asia/Shanghai")
    )
    published_at = published_local.astimezone(timezone.utc).replace(tzinfo=None)
    current = now or utcnow()
    if published_at > current + timedelta(hours=1):
        return []
    if current - published_at > timedelta(hours=48):
        return []

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]
    starts = [index for index, line in enumerate(lines) if re.match(r"^\d{1,2}、", line)]
    items: list[dict] = []
    seen_urls: set[str] = set()
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        section = "\n".join(lines[start:end])
        title_match = re.match(r"^\d{1,2}、\s*(.+)$", lines[start])
        link_match = re.search(r"详情链接\s*[:：]\s*(https?://[^\s]+)", section)
        if not title_match or not link_match:
            continue

        original_url = link_match.group(1).rstrip(".,;，。；、)]）】")
        if any(character in original_url for character in ("\\", "<", ">")):
            continue
        parts = urlsplit(original_url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            continue
        if parts.hostname == "aibase.com" or parts.hostname.endswith(".aibase.com"):
            continue
        if original_url in seen_urls:
            continue

        title = title_match.group(1).strip()[:500]
        if not title:
            continue
        seen_urls.add(original_url)
        items.append(
            {
                "title": title,
                "body": None,
                "author": "AIBase（聚合参考）",
                "url": original_url,
                "published_at": published_at,
                "raw": {
                    "title": title,
                    "link": original_url,
                    "source_page": page_url,
                    "published": published_at.isoformat(),
                    "source_kind": "aggregated_reference",
                },
            }
        )
        if len(items) == _AIBASE_DAILY_LIMIT:
            break
    return items


def _fetch_aibase_daily(list_url: str) -> list[dict]:
    latest_url = _parse_aibase_latest_url(_request_text(list_url), list_url)
    if latest_url is None:
        raise ValueError("AIBase 最新日报链接未找到")
    return _parse_aibase_daily(_request_text(latest_url), latest_url)


def _hn_item_to_item(raw: Any, *, now: datetime | None = None) -> dict | None:
    if not isinstance(raw, dict):
        return None
    if raw.get("type") != "story" or raw.get("deleted") or raw.get("dead"):
        return None

    title = str(raw.get("title") or "").strip()
    if not title or not _HN_AI_PATTERN.search(title):
        return None
    original_url = str(raw.get("url") or "").strip()
    parts = urlsplit(original_url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return None
    if parts.hostname == "news.ycombinator.com":
        return None

    try:
        published_at = datetime.fromtimestamp(int(raw["time"]), tz=timezone.utc).replace(
            tzinfo=None
        )
        score = int(raw.get("score") or 0)
        comments = int(raw.get("descendants") or 0)
        item_id = int(raw["id"])
    except (KeyError, TypeError, ValueError, OSError):
        return None

    current = now or utcnow()
    if published_at > current + timedelta(minutes=5):
        return None
    if current - published_at > timedelta(hours=24):
        return None
    if score < 5 and comments < 3:
        return None

    return {
        "title": title[:500],
        "body": None,
        "author": str(raw.get("by") or "")[:200] or None,
        "url": original_url,
        "published_at": published_at,
        "raw": {
            "title": title[:500],
            "link": original_url,
            "published": published_at.isoformat(),
            "source_kind": "community_signal",
            "hacker_news_url": f"https://news.ycombinator.com/item?id={item_id}",
            "score": score,
            "comments": comments,
        },
    }


def _fetch_hacker_news(new_stories_url: str) -> list[dict]:
    parts = urlsplit(new_stories_url)
    if parts.hostname != "hacker-news.firebaseio.com":
        raise ValueError("Hacker News 必须使用官方 API")
    story_ids = _request_json(new_stories_url)
    if not isinstance(story_ids, list):
        raise ValueError("Hacker News 最新列表格式异常")

    ids = [story_id for story_id in story_ids[:_HN_SCAN_LIMIT] if isinstance(story_id, int)]
    api_root = new_stories_url.rsplit("/", 1)[0]

    def load_story(story_id: int) -> Any:
        try:
            return _request_json(f"{api_root}/item/{story_id}.json")
        except (httpx.HTTPError, ValueError, TypeError):
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        raw_items = list(executor.map(load_story, ids))
    if ids and not any(item is not None for item in raw_items):
        raise ValueError("Hacker News 条目读取全部失败")

    items = [item for raw in raw_items if (item := _hn_item_to_item(raw)) is not None]
    items.sort(key=lambda item: item["published_at"], reverse=True)
    return items[:_HN_RESULT_LIMIT]


def fetch_items(source_type: SourceType, url: str) -> list[dict]:
    """抓取并解析一个信息源，返回条目列表。异常向上抛，由编排层记录失败。"""
    if source_type == SourceType.web_page:
        raise ValueError("官网观察源尚未接入自动采集")
    if source_type == SourceType.x:
        # 占位：真实 X 采集后续接入（见决策备忘）
        return []
    if source_type == SourceType.aibase_daily:
        return _fetch_aibase_daily(url)
    if source_type == SourceType.hacker_news:
        return _fetch_hacker_news(url)

    response = httpx.get(
        url,
        timeout=settings.collect_timeout_seconds,
        follow_redirects=True,
        headers=_HEADERS,
    )
    response.raise_for_status()

    parsed = feedparser.parse(response.content)
    items: list[dict] = []
    for entry in parsed.entries:
        item = _entry_to_item(entry)
        if item:
            items.append(item)
    return items
