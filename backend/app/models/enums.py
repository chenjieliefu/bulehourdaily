"""受控枚举：状态与类型统一用枚举，避免字符串散落。"""
import enum


class SourceType(str, enum.Enum):
    rss = "rss"                      # 官方博客/新闻 RSS/Atom
    github_releases = "github_releases"  # GitHub Releases Atom
    x = "x"                          # X（推特）账号，本阶段占位、不真采
    web_page = "web_page"            # 官网观察源，未接页面采集前保持停用
    aibase_daily = "aibase_daily"    # AIBase 最新一期日报，仅作聚合参考
    hacker_news = "hacker_news"      # Hacker News 官方 API，经 AI 规则筛选


class CredibilityLevel(str, enum.Enum):
    official = "official"            # 官方
    media = "media"                  # 媒体/第三方


class CollectionStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"


class CredibilityLabel(str, enum.Enum):
    official = "official"            # 官方确认
    multi_source = "multi_source"    # 多方报道
    early_signal = "early_signal"    # 早期信号


class EventStatus(str, enum.Enum):
    candidate = "candidate"
    selected = "selected"
    brief = "brief"
    archived = "archived"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class JobKind(str, enum.Enum):
    extract_events = "extract_events"
    generate_report = "generate_report"
    personalized_report = "personalized_report"
    generate_plan = "generate_plan"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class FeedbackStatus(str, enum.Enum):
    want = "want"                      # 想做
    not_interested = "not_interested"  # 不感兴趣
    published = "published"            # 已发布


class PriceType(str, enum.Enum):
    founding = "founding"    # 创始价 ¥29
    standard = "standard"    # 标准价 ¥49


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    expired = "expired"


class MailStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
