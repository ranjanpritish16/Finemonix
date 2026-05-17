# pyrefly: ignore [missing-import]
from celery import Celery

from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "neevfinance",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Auto-discover tasks in backend/tasks/
celery_app.autodiscover_tasks(["backend.tasks"])
