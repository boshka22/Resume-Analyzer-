"""Инициализация Celery приложения."""

from celery import Celery

from app.core.config import settings

__all__ = ['celery_app']

celery_app = Celery(
    'resume_analyzer',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.analyze'],
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)
