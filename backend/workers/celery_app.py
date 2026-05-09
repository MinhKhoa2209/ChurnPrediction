"""
Celery Application Configuration
"""



from celery import Celery

from backend.config import settings

# Create Celery app instance
celery_app = Celery(
    "churn_prediction",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.workers.dataset_tasks",
        "backend.workers.training_tasks",
        "backend.workers.prediction_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)

# Task routing (can be extended for different queues)
celery_app.conf.task_routes = {
    "backend.workers.dataset_tasks.*": {"queue": "datasets"},
    "backend.workers.training_tasks.*": {"queue": "training"},
    "backend.workers.prediction_tasks.*": {"queue": "predictions"},
}
