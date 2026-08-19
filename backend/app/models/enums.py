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
