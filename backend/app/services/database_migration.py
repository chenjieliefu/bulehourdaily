"""应用启动时执行数据库结构升级。"""
from pathlib import Path

from alembic import command
from alembic.config import Config


_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def upgrade_database_schema() -> None:
    """把当前数据库升级到仓库内最新迁移版本。"""
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    command.upgrade(config, "head")
