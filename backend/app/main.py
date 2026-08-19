"""微蓝日报 后端入口（第 1 阶段）。"""
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import collect, source_items, sources, status
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.services.collection import collect_all
from app.services.seed import seed_sources

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sources(db)
    finally:
        db.close()

    scheduler.add_job(
        _scheduled_collect,
        "interval",
        minutes=settings.collect_interval_minutes,
        id="collect",
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

app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(_STATIC_DIR / "index.html"))
