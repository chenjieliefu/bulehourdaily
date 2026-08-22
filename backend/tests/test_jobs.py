"""后台任务提交保护。"""
from datetime import timedelta

from app.core.time import utcnow
from app.models import Job
from app.models.enums import JobKind, JobStatus
from app.services.jobs import _start_or_reuse_job


def test_active_job_is_reused_for_same_kind_and_context(db):
    first_id, first_created = _start_or_reuse_job(db, JobKind.extract_events)
    second_id, second_created = _start_or_reuse_job(db, JobKind.extract_events)

    assert first_created is True
    assert second_created is False
    assert second_id == first_id
    assert db.query(Job).count() == 1


def test_different_job_contexts_can_run_independently(db):
    first_id, _ = _start_or_reuse_job(
        db,
        JobKind.personalized_report,
        {"user_id": 1},
    )
    second_id, second_created = _start_or_reuse_job(
        db,
        JobKind.personalized_report,
        {"user_id": 2},
    )

    assert second_created is True
    assert second_id != first_id


def test_stale_active_job_is_failed_before_retry(db):
    stale = Job(
        kind=JobKind.generate_report,
        status=JobStatus.running,
        created_at=utcnow() - timedelta(minutes=11),
    )
    db.add(stale)
    db.commit()

    new_id, created = _start_or_reuse_job(db, JobKind.generate_report)

    db.refresh(stale)
    assert created is True
    assert new_id != stale.id
    assert stale.status == JobStatus.failed
    assert stale.finished_at is not None
