"""微蓝日报 后端入口（第 1 阶段）。"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask, BackgroundTasks

from app.api import (
    admin,
    auth,
    collect,
    events,
    feedback,
    jobs,
    personalized,
    plans,
    product_feedback,
    profile,
    reports,
    site_content,
    source_items,
    sources,
    status,
    subscriptions,
)
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.services.collection import collect_all
from app.services.database_backup import DatabaseBackupError, backup_database, restore_database
from app.services.seed import (
    seed_configured_invite_codes,
    seed_operator_account,
    seed_sources,
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _safe_database_backup() -> None:
    """尽力备份；运行中失败要留日志，但不让用户请求或定时任务崩溃。"""
    try:
        backup_database()
    except DatabaseBackupError:
        logger.exception("SQLite 数据库备份失败")


def _scheduled_collect():
    """定时采集：失败只记录，不让进程崩溃。"""
    db = SessionLocal()
    try:
        collect_all(db)
    except Exception:  # noqa: BLE001 —— 定时任务兜底
        logger.exception("定时采集失败")
    finally:
        db.close()
    _safe_database_backup()


def _daily_report_job():
    """每天北京时间 08:00：生产、质量检查并自动公开当日日报。"""
    try:
        from datetime import datetime

        from app.models.enums import JobKind
        from app.services.jobs import run_now

        report_date = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
        run_now(JobKind.daily_publication, {"report_date": report_date})
    except Exception:  # noqa: BLE001 —— 定时任务兜底
        logger.exception("日报自动发布任务启动失败")
    _safe_database_backup()


def _scheduled_database_backup():
    """周期兜底备份，覆盖后台线程或非 HTTP 路径产生的数据。"""
    _safe_database_backup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    restored = restore_database()
    if restored:
        # Engine 通常尚未建立连接；显式释放可避免测试或特殊启动器提前建连。
        engine.dispose()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sources(db)
        seed_configured_invite_codes(db)
        seed_operator_account(db)
    finally:
        db.close()

    # 首次启动或完成恢复后立即建立一个可用云端版本。
    _safe_database_backup()

    scheduler.add_job(
        _scheduled_collect,
        "interval",
        minutes=settings.collect_interval_minutes,
        id="collect",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        _daily_report_job,
        CronTrigger(hour=8, minute=0, timezone=ZoneInfo("Asia/Shanghai")),
        id="daily_report",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        _scheduled_database_backup,
        "interval",
        minutes=settings.tos_backup_interval_minutes,
        id="database_backup",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        _safe_database_backup()


app = FastAPI(title="微蓝日报", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def backup_after_mutation(request, call_next):
    """成功的写请求结束后执行备份，缩短用户数据尚未进入云端的窗口。"""
    response = await call_next(request)
    if request.method in _MUTATING_METHODS and 200 <= response.status_code < 400:
        backup_task = BackgroundTask(_safe_database_backup)
        if response.background is None:
            response.background = backup_task
        else:
            response.background = BackgroundTasks([response.background, backup_task])
    return response

app.include_router(sources.router, prefix="/api/v1")
app.include_router(source_items.router, prefix="/api/v1")
app.include_router(collect.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(site_content.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(personalized.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(product_feedback.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(_STATIC_DIR / "index.html"))
