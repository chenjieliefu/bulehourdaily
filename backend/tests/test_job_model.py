"""任务状态机持久化测试。"""
from app.models import Job
from app.models.enums import JobKind, JobStatus


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
