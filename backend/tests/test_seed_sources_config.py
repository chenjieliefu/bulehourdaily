"""首批信息源配置必须与已确认的 10 家保持一致。"""
import json
from pathlib import Path

from app.models.enums import SourceType


_SEED_PATH = Path(__file__).resolve().parents[1] / "app" / "core" / "seed_sources.json"


def test_seed_sources_are_the_confirmed_ten_groups():
    sources = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    core = [source for source in sources if source.get("source_tier") != "supplemental"]

    assert {source["source_group"] for source in core} == {
        "OpenAI",
        "Google AI / DeepMind",
        "Anthropic",
        "Meta AI",
        "Midjourney",
        "Runway",
        "DeepSeek",
        "Qwen",
        "Kimi",
        "MiniMax",
    }
    assert len(core) == 11  # Google AI 与 DeepMind 各有一个官方 Feed
    assert all(source["credibility_level"] == "official" for source in core)
    assert not any(source["type"] in {"x", "github_releases"} for source in core)


def test_only_supported_feeds_are_enabled_for_automatic_collection():
    sources = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    core = [source for source in sources if source.get("source_tier") != "supplemental"]
    enabled = [source for source in core if source["enabled"]]
    observation = [source for source in core if not source["enabled"]]

    assert {source["name"] for source in enabled} == {
        "OpenAI News",
        "Google AI Blog",
        "Google DeepMind Blog",
        "Midjourney Updates",
    }
    assert all(source["type"] == SourceType.rss.value for source in enabled)
    assert all(source["type"] == SourceType.web_page.value for source in observation)


def test_only_approved_supplemental_sources_are_configured():
    sources = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    supplemental = [
        source for source in sources if source.get("source_tier") == "supplemental"
    ]

    assert {source["name"] for source in supplemental} == {
        "AIBase 最新 AI 日报",
        "Hacker News AI 线索",
    }
    assert {source["type"] for source in supplemental} == {
        SourceType.aibase_daily.value,
        SourceType.hacker_news.value,
    }
    assert all(source["enabled"] for source in supplemental)
    assert all(source["credibility_level"] == "media" for source in supplemental)
    assert not any("aihot.virxact.com" in source["url"] for source in sources)
