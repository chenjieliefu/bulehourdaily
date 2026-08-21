"""微蓝日报 后端入口（第 1 阶段）。"""
from contextlib import asynccontextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
from app.services.seed import seed_invite_codes, seed_operator_account, seed_sources

_STATIC_DIR = Path(__file__).resolve().parent / "static"

scheduler = BackgroundScheduler()


def _scheduled_collect():
    """定时采集：失败只记录，不让进程崩溃。"""
    db = SessionLocal()
    try:
        collect_all(db)
    except Exception:  # noqa: BLE001 —— 定时任务兜底
        pass
    finally:
        db.close()


def _daily_report_job():
    """每天北京时间 08:00：提取事件 + 生成通用日报（草稿，待质检）。"""
    db = SessionLocal()
    try:
        from app.services.event_extraction import extract_events
        from app.services.report_generation import generate_report

        extract_events(db)
        generate_report(db)
    except Exception:  # noqa: BLE001 —— 定时任务兜底
        pass
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sources(db)
        seed_invite_codes(db)
        seed_operator_account(db)
    finally:
        db.close()

    scheduler.add_job(
        _scheduled_collect,
        "interval",
        minutes=settings.collect_interval_minutes,
        id="collect",
        replace_existing=True,
    )
    scheduler.add_job(
        _daily_report_job,
        CronTrigger(hour=8, minute=0, timezone=ZoneInfo("Asia/Shanghai")),
        id="daily_report",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="微蓝日报", version="0.1.0", lifespan=lifespan)

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
