import os
from celery import Celery

celery_app = Celery("booking_worker")

celery_app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_ignore_result=True,
)

import shared.tasks.booking_task