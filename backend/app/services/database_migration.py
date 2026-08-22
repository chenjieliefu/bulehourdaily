"""应用启动时执行数据库结构升级。"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import settings


_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_LEGACY_BASELINE = "c61f8a2d7e04"
_LEGACY_REQUIRED_COLUMNS = {
    "job": {"context"},
    "topic_recommendation": {"reviewed"},
    "user": {"is_operator"},
}
_LEGACY_REQUIRED_TABLES = {
    "collection_run",
    "creation_plan",
    "creator_profile",
    "daily_report",
    "event_evidence",
    "hot_brief",
    "hot_event",
    "invite_code",
    "job",
    "mail_delivery",
    "personalized_report",
    "personalized_topic",
    "product_feedback",
    "site_content",
    "source",
    "source_item",
    "subscription",
    "topic_feedback",
    "topic_recommendation",
    "user",
}


def _stamp_legacy_database(config: Config) -> None:
    """为早期由 ``create_all`` 建成、没有迁移版本表的数据库登记基线。"""
    migration_engine = create_engine(settings.database_url)
    try:
        inspector = inspect(migration_engine)
        tables = set(inspector.get_table_names())
        if not tables or "alembic_version" in tables:
            return

        missing_tables = _LEGACY_REQUIRED_TABLES - tables
        missing_columns = {
            table: required - {column["name"] for column in inspector.get_columns(table)}
            for table, required in _LEGACY_REQUIRED_COLUMNS.items()
            if table in tables
            and required - {column["name"] for column in inspector.get_columns(table)}
        }
        if missing_tables or missing_columns:
            raise RuntimeError(
                "检测到未登记版本的历史数据库，但结构不满足安全迁移基线："
                f"缺少表={sorted(missing_tables)}，缺少字段={missing_columns}"
            )
    finally:
        migration_engine.dispose()

    command.stamp(config, _LEGACY_BASELINE)


def upgrade_database_schema() -> None:
    """把当前数据库升级到仓库内最新迁移版本。"""
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    _stamp_legacy_database(config)
    command.upgrade(config, "head")
