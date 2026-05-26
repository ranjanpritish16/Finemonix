# pyrefly: ignore [missing-import]
import sys

from celery import Celery

from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "Finemonix",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    worker_prefetch_multiplier=1,
)

if sys.platform.startswith("win"):
    celery_app.conf.worker_pool = "solo"
    celery_app.conf.worker_concurrency = 1

# Auto-discover tasks in backend/tasks/
celery_app.autodiscover_tasks(["backend.tasks"])

# Explicitly import tasks to ensure registration
from backend.tasks import processing_tasks
