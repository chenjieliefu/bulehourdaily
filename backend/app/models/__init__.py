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
from .user import User
from .invite_code import InviteCode
from .creator_profile import CreatorProfile
from .personalized_report import PersonalizedReport
from .personalized_topic import PersonalizedTopic

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
    "User",
    "InviteCode",
    "CreatorProfile",
    "PersonalizedReport",
    "PersonalizedTopic",
]
