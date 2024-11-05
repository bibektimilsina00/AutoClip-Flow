import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()


celery_worker = Celery(
    "worker",
    backend=os.getenv("CELERY_BACKEND"),
    broker=os.getenv("CELERY_BROKER"),
    include=["celery_worker.task"],
)

# Additional configuration for Celery
celery_worker.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    # Optional: You can set the worker name to distinguish multiple workers in Flower
    worker_prefetch_multiplier=1,  # Ensures tasks are executed in order
)

# Initially, do not set up any beat_schedule
celery_worker.conf.beat_schedule = {}

__all__ = ["celery_worker"]
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# celery -A celery_worker.celery_worker worker --loglevel=info
# celery -A celery_worker.celery_worker flower
