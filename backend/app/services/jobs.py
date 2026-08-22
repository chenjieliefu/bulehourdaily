"""后台任务执行器：提交 + 轮询。任务状态持久化，可恢复查询。"""
import threading
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.time import utcnow
from app.models import Job
from app.models.enums import JobKind, JobStatus


_STALE_JOB_AFTER = timedelta(minutes=10)


def _run_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        job.status = JobStatus.running
        job.started_at = utcnow()
        db.commit()

        if job.kind == JobKind.extract_events:
            from .event_extraction import extract_events

            result = extract_events(db)
            job.result_ref = f"events:{result['events_created']}"
        elif job.kind == JobKind.generate_report:
            from .report_generation import generate_report

            result = generate_report(db)
            job.result_ref = f"report:{result['report_id']}"
        elif job.kind == JobKind.daily_publication:
            from datetime import date

            from .daily_publication import run_daily_publication

            raw_date = (job.context or {}).get("report_date")
            target_date = date.fromisoformat(raw_date) if raw_date else None
            result = run_daily_publication(db, report_date=target_date)
            job.result_ref = f"daily:{result['report_id']}:{result['status']}"
        elif job.kind == JobKind.personalized_report:
            from .personalization import generate_personalized

            user_id = (job.context or {}).get("user_id")
            if not user_id:
                raise ValueError("缺少 user_id")
            result = generate_personalized(db, int(user_id))
            job.result_ref = f"personalized:{result['report_id']}"
        elif job.kind == JobKind.generate_plan:
            from .creation_plan import generate_plan

            ctx = job.context or {}
            user_id = ctx.get("user_id")
            topic_id = ctx.get("topic_id")
            if not user_id or not topic_id:
                raise ValueError("缺少 user_id/topic_id")
            result = generate_plan(db, int(user_id), int(topic_id))
            job.result_ref = f"plan:{result['plan_id']}"
        else:
            raise ValueError(f"未知任务类型: {job.kind}")

        job.status = JobStatus.success
        job.finished_at = utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001 —— 记录失败，不崩溃
        db.rollback()
        job = db.get(Job, job_id)
        if job is not None:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:2000]
            job.finished_at = utcnow()
            db.commit()
    finally:
        db.close()


def start_job(kind: JobKind, context: dict | None = None) -> int:
    """创建任务并后台执行，返回 job id。"""
    db = SessionLocal()
    try:
        job = Job(kind=kind, status=JobStatus.pending, context=context)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def _start_or_reuse_job(
    db: Session,
    kind: JobKind,
    context: dict | None = None,
) -> tuple[int, bool]:
    """复用同类同上下文的活动任务，避免重复模型调用和并发写入。"""
    normalized_context = context or None
    stale_before = utcnow() - _STALE_JOB_AFTER
    active_jobs = (
        db.query(Job)
        .filter(
            Job.kind == kind,
            Job.status.in_([JobStatus.pending, JobStatus.running]),
        )
        .order_by(Job.id.desc())
        .all()
    )
    for active in active_jobs:
        if (active.context or None) != normalized_context:
            continue
        if active.created_at >= stale_before:
            return active.id, False
        active.status = JobStatus.failed
        active.error_message = "任务运行超过 10 分钟，已允许重新提交"
        active.finished_at = utcnow()

    job = Job(kind=kind, status=JobStatus.pending, context=normalized_context)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id, True


def run_in_background(kind: JobKind, context: dict | None = None) -> int:
    db = SessionLocal()
    try:
        job_id, created = _start_or_reuse_job(db, kind, context)
    finally:
        db.close()
    if created:
        threading.Thread(target=_run_job, args=(job_id,), daemon=True).start()
    return job_id


def run_now(kind: JobKind, context: dict | None = None) -> int:
    """同步执行并持久化任务状态，供调度器使用。"""
    job_id = start_job(kind, context)
    _run_job(job_id)
    return job_id
