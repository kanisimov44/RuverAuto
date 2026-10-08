from celery import Celery

from app.config import settings

celery_app = Celery(
    "ruverauto",
    broker=settings.REDIS_URL,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    # В тестах задачи выполняются сразу, без брокера и воркера
    task_always_eager=settings.MODE == "TEST",
    # Если брокер недоступен, админка не должна зависать на сохранении
    task_publish_retry_policy={"max_retries": 1, "interval_start": 0, "interval_step": 0.5},
    broker_connection_retry_on_startup=True,
)
