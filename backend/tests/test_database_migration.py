"""数据库启动迁移测试。"""
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.services.database_migration import upgrade_database_schema


_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _columns(path: Path, table: str) -> set[str]:
    with sqlite3.connect(path) as connection:
        return {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }


def test_upgrade_database_schema_applies_pending_migrations(tmp_path, monkeypatch):
    database_path = tmp_path / "startup-migration.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    command.upgrade(config, "c61f8a2d7e04")
    assert "is_published" not in _columns(database_path, "topic_recommendation")

    upgrade_database_schema()
    upgrade_database_schema()

    assert "is_published" in _columns(database_path, "topic_recommendation")


def test_upgrade_database_schema_adopts_unversioned_legacy_database(
    tmp_path, monkeypatch,
):
    database_path = tmp_path / "legacy-database.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    command.upgrade(config, "c61f8a2d7e04")
    with sqlite3.connect(database_path) as connection:
        connection.execute("DROP TABLE alembic_version")
    assert "is_published" not in _columns(database_path, "topic_recommendation")

    upgrade_database_schema()

    assert "is_published" in _columns(database_path, "topic_recommendation")
    with sqlite3.connect(database_path) as connection:
        version = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert version == ("9b7c31f2a640",)
