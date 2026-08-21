import sqlite3
from pathlib import Path

import pytest
from starlette.background import BackgroundTask
from starlette.responses import Response

from app.main import backup_after_mutation
from app.services.database_backup import (
    DatabaseBackupConfig,
    DatabaseBackupError,
    backup_database,
    restore_database,
    runtime_backup_config,
    sqlite_path_from_url,
)


class FakeNotFoundError(Exception):
    code = "NoSuchKey"
    status_code = 404


class FakeTosClient:
    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}

    def put_object_from_file(self, bucket: str, key: str, file_path: str):
        self.objects[(bucket, key)] = Path(file_path).read_bytes()

    def get_object(self, bucket: str, key: str):
        try:
            content = self.objects[(bucket, key)]
        except KeyError as exc:
            raise FakeNotFoundError from exc
        midpoint = max(1, len(content) // 2)
        return iter((content[:midpoint], content[midpoint:]))


class FailingUploadClient(FakeTosClient):
    def put_object_from_file(self, bucket: str, key: str, file_path: str):
        raise OSError("isolated upload failure")


class FailingDownloadClient(FakeTosClient):
    def get_object(self, bucket: str, key: str):
        raise TimeoutError("isolated download failure")


def _config(path: Path) -> DatabaseBackupConfig:
    return DatabaseBackupConfig(
        database_path=path,
        access_key_id="isolated-test-ak",
        secret_access_key="isolated-test-sk",
        bucket="isolated-test-bucket",
        endpoint="tos.example.invalid",
        region="test-region",
    )


def _create_database(path: Path, value: str) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample (value) VALUES (?)", (value,))
        connection.commit()


def _read_value(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT value FROM sample").fetchone()[0]


def test_sqlite_path_from_url_supports_relative_and_absolute_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert sqlite_path_from_url("sqlite:///data/weilan.db") == tmp_path / "data/weilan.db"
    assert sqlite_path_from_url("sqlite:////tmp/weilan.db") == Path("/tmp/weilan.db").resolve()
    assert sqlite_path_from_url("sqlite:///:memory:") is None
    assert sqlite_path_from_url("postgresql://example.invalid/db") is None


def test_backup_and_restore_round_trip(tmp_path):
    source = tmp_path / "source.db"
    restored = tmp_path / "restored.db"
    client = FakeTosClient()
    _create_database(source, "round-trip")

    assert backup_database(_config(source), client) is True
    assert restore_database(_config(restored), client) is True
    assert _read_value(restored) == "round-trip"


def test_backup_is_a_consistent_sqlite_snapshot(tmp_path):
    source = tmp_path / "source.db"
    downloaded = tmp_path / "downloaded.db"
    client = FakeTosClient()
    _create_database(source, "consistent")

    assert backup_database(_config(source), client) is True
    downloaded.write_bytes(client.objects[("isolated-test-bucket", "database/weilan.db")])

    with sqlite3.connect(downloaded) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert _read_value(downloaded) == "consistent"


def test_restore_never_overwrites_existing_local_database(tmp_path):
    local = tmp_path / "local.db"
    remote = tmp_path / "remote.db"
    client = FakeTosClient()
    _create_database(local, "local-newer")
    _create_database(remote, "remote-older")
    assert backup_database(_config(remote), client) is True

    assert restore_database(_config(local), client) is False
    assert _read_value(local) == "local-newer"


def test_restore_allows_first_start_when_remote_object_does_not_exist(tmp_path):
    target = tmp_path / "new.db"

    assert restore_database(_config(target), FakeTosClient()) is False
    assert not target.exists()


def test_restore_rejects_corrupt_remote_database(tmp_path):
    target = tmp_path / "target.db"
    client = FakeTosClient()
    client.objects[("isolated-test-bucket", "database/weilan.db")] = b"not-a-sqlite-database"

    with pytest.raises(DatabaseBackupError, match="无法打开"):
        restore_database(_config(target), client)

    assert not target.exists()


def test_upload_failure_releases_lock_and_removes_snapshot(tmp_path):
    source = tmp_path / "source.db"
    _create_database(source, "retry")

    with pytest.raises(DatabaseBackupError, match="上传"):
        backup_database(_config(source), FailingUploadClient())

    assert list(tmp_path.glob(".weilan-*.backup.db")) == []
    assert backup_database(_config(source), FakeTosClient()) is True


def test_download_failure_never_creates_empty_database(tmp_path):
    target = tmp_path / "target.db"

    with pytest.raises(DatabaseBackupError, match="下载"):
        restore_database(_config(target), FailingDownloadClient())

    assert not target.exists()


def test_partial_runtime_configuration_is_rejected(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'db.sqlite'}"
    monkeypatch.setattr("app.services.database_backup.settings.database_url", database_url)
    monkeypatch.setattr("app.services.database_backup.settings.tos_access_key_id", "isolated-ak")
    monkeypatch.setattr("app.services.database_backup.settings.tos_secret_access_key", "")
    monkeypatch.setattr("app.services.database_backup.settings.tos_bucket", "")
    monkeypatch.setattr("app.services.database_backup.settings.tos_endpoint", "")
    monkeypatch.setattr("app.services.database_backup.settings.tos_region", "")

    with pytest.raises(DatabaseBackupError, match="配置不完整"):
        runtime_backup_config()


@pytest.mark.asyncio
async def test_successful_mutation_runs_existing_task_then_database_backup(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("app.main._safe_database_backup", lambda: calls.append("backup"))

    class Request:
        method = "PATCH"

    async def call_next(_request):
        return Response(
            status_code=200,
            background=BackgroundTask(lambda: calls.append("existing")),
        )

    response = await backup_after_mutation(Request(), call_next)
    await response.background()

    assert calls == ["existing", "backup"]


@pytest.mark.asyncio
async def test_failed_mutation_does_not_schedule_database_backup(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("app.main._safe_database_backup", lambda: calls.append("backup"))

    class Request:
        method = "POST"

    async def call_next(_request):
        return Response(status_code=500)

    response = await backup_after_mutation(Request(), call_next)

    assert response.background is None
    assert calls == []
