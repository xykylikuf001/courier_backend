from celery import Celery, Task
from app.conf.config import settings

celery_app = Celery("worker", broker=settings.REDIS_URL)

celery_app.conf.broker_connection_retry_on_startup = True

celery_app.autodiscover_tasks([
    'app.contrib.account.tasks',
])


celery_app.conf.task_routes = {"app.worker.test_celery": "main-queue"}
