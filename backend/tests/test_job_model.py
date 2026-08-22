"""任务状态机持久化测试。"""
from sqlalchemy.orm import sessionmaker

from app.models import Job
from app.models.enums import JobKind, JobStatus
from app.services import daily_publication as daily_mod
from app.services import jobs as jobs_mod


def test_job_status_transitions_persist(db):
    job = Job(kind=JobKind.extract_events, status=JobStatus.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    job.status = JobStatus.running
    db.commit()
    job.status = JobStatus.success
    db.commit()

    loaded = db.get(Job, job.id)
    assert loaded.status == JobStatus.success
    assert loaded.kind == JobKind.extract_events


def test_daily_publication_job_records_success(db, monkeypatch):
    monkeypatch.setattr(jobs_mod, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(
        daily_mod,
        "run_daily_publication",
        lambda _db, report_date=None: {
            "report_id": 42,
            "status": "published",
        },
    )

    job_id = jobs_mod.run_now(
        JobKind.daily_publication,
        {"report_date": "2026-08-23"},
    )

    db.expire_all()
    job = db.get(Job, job_id)
    assert job.status == JobStatus.success
    assert job.result_ref == "daily:42:published"
    assert job.error_message is None
    assert job.started_at is not None
    assert job.finished_at is not None


def test_daily_publication_job_records_quality_failure(db, monkeypatch):
    monkeypatch.setattr(jobs_mod, "SessionLocal", sessionmaker(bind=db.get_bind()))

    def fail_quality(_db, report_date=None):
        raise daily_mod.DailyPublicationQualityError("主选题没有原始证据")

    monkeypatch.setattr(daily_mod, "run_daily_publication", fail_quality)

    job_id = jobs_mod.run_now(
        JobKind.daily_publication,
        {"report_date": "2026-08-23"},
    )

    db.expire_all()
    job = db.get(Job, job_id)
    assert job.status == JobStatus.failed
    assert job.error_message == "主选题没有原始证据"
    assert job.finished_at is not None
