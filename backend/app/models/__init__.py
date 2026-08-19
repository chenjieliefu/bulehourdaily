"""模型统一出口：导入即注册到 Base.metadata（Alembic 依赖此行为）。"""
from .source import Source
from .source_item import SourceItem
from .collection_run import CollectionRun
from .hot_event import HotEvent
from .event_evidence import EventEvidence
from .daily_report import DailyReport
from .topic_recommendation import TopicRecommendation
from .hot_brief import HotBrief
from .job import Job

__all__ = [
    "Source",
    "SourceItem",
    "CollectionRun",
    "HotEvent",
    "EventEvidence",
    "DailyReport",
    "TopicRecommendation",
    "HotBrief",
    "Job",
]
