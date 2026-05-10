from celery import Celery

from backend.config import settings

celery_app = Celery(
    "churn_prediction",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.workers.dataset_tasks",
        "backend.workers.training_tasks",
        "backend.workers.prediction_tasks",
    ],
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)


celery_app.conf.task_routes = {
    "backend.workers.dataset_tasks.*": {"queue": "datasets"},
    "backend.workers.training_tasks.*": {"queue": "training"},
    "backend.workers.prediction_tasks.*": {"queue": "predictions"},
}
