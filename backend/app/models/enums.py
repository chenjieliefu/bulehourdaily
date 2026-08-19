"""受控枚举：状态与类型统一用枚举，避免字符串散落。"""
import enum


class SourceType(str, enum.Enum):
    rss = "rss"                      # 官方博客/新闻 RSS/Atom
    github_releases = "github_releases"  # GitHub Releases Atom
    x = "x"                          # X（推特）账号，本阶段占位、不真采


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


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
