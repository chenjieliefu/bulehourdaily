"""后台任务执行器：提交 + 轮询。任务状态持久化，可恢复查询。"""
import threading
from datetime import datetime

from app.core.database import SessionLocal
from app.models import Job
from app.models.enums import JobKind, JobStatus


def _run_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        job.status = JobStatus.running
        job.started_at = datetime.utcnow()
        db.commit()

        if job.kind == JobKind.extract_events:
            from .event_extraction import extract_events

            result = extract_events(db)
            job.result_ref = f"events:{result['events_created']}"
        elif job.kind == JobKind.generate_report:
            from .report_generation import generate_report

            result = generate_report(db)
            job.result_ref = f"report:{result['report_id']}"
        else:
            raise ValueError(f"未知任务类型: {job.kind}")

        job.status = JobStatus.success
        job.finished_at = datetime.utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001 —— 记录失败，不崩溃
        db.rollback()
        job = db.get(Job, job_id)
        if job is not None:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:2000]
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def start_job(kind: JobKind) -> int:
    """创建任务并后台执行，返回 job id。"""
    db = SessionLocal()
    try:
        job = Job(kind=kind, status=JobStatus.pending)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def run_in_background(kind: JobKind) -> int:
    job_id = start_job(kind)
    threading.Thread(target=_run_job, args=(job_id,), daemon=True).start()
    return job_id
