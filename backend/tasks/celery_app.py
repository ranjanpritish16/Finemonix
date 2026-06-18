# pyrefly: ignore [missing-import]
import sys
from celery import Celery
from celery.schedules import crontab
from backend.config import get_settings
import backend.tasks.nlp_tasks  # noqa: F401
import backend.tasks.extraction_tasks  # noqa: F401

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

# ------------------------------------------------------------------
# Celery Beat schedule
# ------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    # Scrape all watched companies every 30 minutes
    "scrape-all-watched-every-30min": {
        "task": "tasks.scrape_all_watched",
        "schedule": crontab(minute="*/30"),
    },
}

# Auto-discover tasks in backend/tasks/
celery_app.autodiscover_tasks(["backend.tasks"])

# Explicitly import tasks to ensure registration
import backend.tasks.processing_tasks  # noqa: F401
import backend.tasks.scraper_tasks     # noqa: F401