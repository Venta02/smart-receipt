"""Celery application config for async batch processing."""

from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "smart_receipt",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=10 * 60,
    task_soft_time_limit=8 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
