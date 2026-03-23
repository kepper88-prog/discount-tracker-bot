from celery import Celery
from shared.config import settings

celery_app = Celery(
    "discount_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.price_checker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=15 * 60,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Периодические задачи
celery_app.conf.beat_schedule = {
    "check-all-prices-every-hour": {
        "task": "tasks.price_checker.check_all_prices",
        "schedule": 3600.0,  # каждый час
        "options": {"queue": "price_checks"}
    },
    "cleanup-old-history-daily": {
        "task": "tasks.price_checker.cleanup_price_history",
        "schedule": 86400.0,  # раз в день
        "args": (30,)  # хранить 30 дней
    },
}