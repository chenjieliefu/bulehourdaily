"""SQLite 到 TOS 的备份与启动恢复。

只使用 SQLite 在线备份 API 生成一致性快照，绝不直接复制正在写入的数据库文件。
云端固定对象名依赖 TOS 桶版本控制保存历史版本。
"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

_backup_lock = threading.Lock()
_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchObject", "ObjectNotExist"}


class DatabaseBackupError(RuntimeError):
    """备份配置、上传、下载或完整性校验失败。"""


class TosClient(Protocol):
    def put_object_from_file(self, bucket: str, key: str, file_path: str): ...

    def get_object(self, bucket: str, key: str): ...


@dataclass(frozen=True)
class DatabaseBackupConfig:
    database_path: Path
    access_key_id: str
    secret_access_key: str
    bucket: str
    endpoint: str
    region: str
    object_key: str = "database/weilan.db"
    request_timeout_seconds: int = 20


def sqlite_path_from_url(database_url: str) -> Path | None:
    """从本地 SQLite URL 解析数据库文件；内存或非 SQLite 数据库返回 None。"""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url[len(prefix) :]
    if not raw_path or raw_path == ":memory:":
        return None
    return Path(raw_path).expanduser().resolve()


def runtime_backup_config() -> DatabaseBackupConfig | None:
    """读取运行时配置；全部留空表示关闭，部分配置则拒绝启动。"""
    database_path = sqlite_path_from_url(settings.database_url)
    if database_path is None:
        return None

    values = {
        "TOS_ACCESS_KEY_ID": settings.tos_access_key_id,
        "TOS_SECRET_ACCESS_KEY": settings.tos_secret_access_key,
        "TOS_BUCKET": settings.tos_bucket,
        "TOS_ENDPOINT": settings.tos_endpoint,
        "TOS_REGION": settings.tos_region,
    }
    configured = [name for name, value in values.items() if value.strip()]
    if not configured:
        return None
    missing = [name for name, value in values.items() if not value.strip()]
    if missing:
        raise DatabaseBackupError(f"TOS 备份配置不完整，缺少：{', '.join(missing)}")
    if settings.tos_backup_interval_minutes <= 0:
        raise DatabaseBackupError("TOS_BACKUP_INTERVAL_MINUTES 必须大于 0")
    if settings.tos_request_timeout_seconds <= 0:
        raise DatabaseBackupError("TOS_REQUEST_TIMEOUT_SECONDS 必须大于 0")

    return DatabaseBackupConfig(
        database_path=database_path,
        access_key_id=settings.tos_access_key_id,
        secret_access_key=settings.tos_secret_access_key,
        bucket=settings.tos_bucket,
        endpoint=settings.tos_endpoint,
        region=settings.tos_region,
        object_key=settings.tos_database_object_key.strip() or "database/weilan.db",
        request_timeout_seconds=settings.tos_request_timeout_seconds,
    )


def _new_client(config: DatabaseBackupConfig) -> TosClient:
    try:
        import tos
    except ImportError as exc:  # pragma: no cover - 生产依赖缺失才会发生
        raise DatabaseBackupError("未安装 TOS Python SDK") from exc

    timeout = config.request_timeout_seconds
    return tos.TosClientV2(
        config.access_key_id,
        config.secret_access_key,
        config.endpoint,
        config.region,
        max_retry_count=2,
        request_timeout=timeout,
        connection_time=min(timeout, 10),
        socket_timeout=timeout,
        enable_crc=True,
    )


def _sqlite_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _assert_sqlite_integrity(path: Path) -> None:
    try:
        with sqlite3.connect(_sqlite_uri(path), uri=True) as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()
    except sqlite3.Error as exc:
        raise DatabaseBackupError("SQLite 备份文件无法打开") from exc
    if result != ("ok",):
        raise DatabaseBackupError("SQLite 备份文件完整性校验失败")


def _create_sqlite_snapshot(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise DatabaseBackupError("本地 SQLite 数据库不存在")
    try:
        with sqlite3.connect(_sqlite_uri(source), uri=True) as source_db:
            with sqlite3.connect(destination) as snapshot_db:
                source_db.backup(snapshot_db)
    except sqlite3.Error as exc:
        raise DatabaseBackupError("生成 SQLite 一致性快照失败") from exc
    _assert_sqlite_integrity(destination)


def _temporary_path(parent: Path, suffix: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    handle, raw_path = tempfile.mkstemp(prefix=".weilan-", suffix=suffix, dir=parent)
    os.close(handle)
    return Path(raw_path)


def _is_not_found_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    status_code = getattr(exc, "status_code", None)
    return code in _NOT_FOUND_CODES or status_code == 404


def backup_database(
    config: DatabaseBackupConfig | None = None,
    client: TosClient | None = None,
) -> bool:
    """生成一致性快照并上传；未启用或无本地数据库时返回 False。"""
    config = config or runtime_backup_config()
    if config is None or not config.database_path.is_file():
        return False
    if not _backup_lock.acquire(blocking=False):
        logger.info("已有数据库备份正在执行，本次跳过")
        return False

    snapshot_path: Path | None = None
    try:
        snapshot_path = _temporary_path(config.database_path.parent, ".backup.db")
        _create_sqlite_snapshot(config.database_path, snapshot_path)
        (client or _new_client(config)).put_object_from_file(
            config.bucket,
            config.object_key,
            str(snapshot_path),
        )
        logger.info("SQLite 数据库已备份到 TOS：%s", config.object_key)
        return True
    except DatabaseBackupError:
        raise
    except Exception as exc:  # SDK 异常统一收口，日志不包含凭据
        raise DatabaseBackupError("上传 SQLite 备份到 TOS 失败") from exc
    finally:
        if snapshot_path is not None:
            snapshot_path.unlink(missing_ok=True)
        _backup_lock.release()


def restore_database(
    config: DatabaseBackupConfig | None = None,
    client: TosClient | None = None,
) -> bool:
    """本地数据库不存在时下载最新备份，校验后原子替换。"""
    config = config or runtime_backup_config()
    if config is None:
        return False
    if config.database_path.is_file() and config.database_path.stat().st_size > 0:
        logger.info("本地 SQLite 数据库已存在，跳过 TOS 恢复")
        return False

    restore_path = _temporary_path(config.database_path.parent, ".restore.db")
    response = None
    try:
        try:
            response = (client or _new_client(config)).get_object(config.bucket, config.object_key)
        except Exception as exc:
            if _is_not_found_error(exc):
                logger.info("TOS 中尚无 SQLite 备份，按首次启动继续")
                return False
            raise DatabaseBackupError("从 TOS 下载 SQLite 备份失败") from exc

        with restore_path.open("wb") as destination:
            for chunk in response:
                if chunk:
                    destination.write(chunk)
            destination.flush()
            os.fsync(destination.fileno())

        _assert_sqlite_integrity(restore_path)
        os.chmod(restore_path, 0o600)
        os.replace(restore_path, config.database_path)
        logger.info("SQLite 数据库已从 TOS 恢复：%s", config.object_key)
        return True
    except DatabaseBackupError:
        raise
    except Exception as exc:
        raise DatabaseBackupError("恢复 SQLite 备份失败") from exc
    finally:
        close = getattr(response, "close", None)
        if not callable(close):
            close = getattr(getattr(response, "content", None), "close", None)
        if callable(close):
            close()
        restore_path.unlink(missing_ok=True)
