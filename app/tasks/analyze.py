"""Celery таск для фонового анализа резюме."""

import asyncio

from celery import Task

from app.celery_app import celery_app
from app.core.database import async_session_maker
from app.graph.builder import build_resume_graph
from app.repositories.resume import ResumeRepository
from app.schemas.v1.resume import (
    AnalysisStatus,
    CriteriaScore,
    ResumeAnalysisResponse,
)

__all__ = ['analyze_resume_task']

_graph = build_resume_graph()


async def _save_to_db(response: ResumeAnalysisResponse) -> int:
    """Сохраняет результат в БД. Возвращает ID записи."""
    async with async_session_maker() as session:
        repo = ResumeRepository(session=session)
        model = await repo.create(response=response)
        return model.id_


@celery_app.task(
    name='analyze_resume',
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def analyze_resume_task(
    self: Task,
    resume_text: str,
    file_name: str | None,
    callback_url: str | None = None,
) -> dict:
    """Запускает граф и сохраняет результат в БД.

    Args:
        resume_text: Текст резюме.
        file_name: Имя файла.
        callback_url: URL для webhook уведомления (опционально).

    Returns:
        dict: Сериализованный результат анализа.
    """
    try:
        result = _graph.invoke(
            {
                'resume_text': resume_text,
                'skills_analysis': {},
                'experience_analysis': {},
                'structure_analysis': {},
                'language_analysis': {},
                'scores': [],
                'final_report': {},
            }
        )

        report = result['final_report']
        criteria = {
            key: CriteriaScore(
                score=val['score'],
                feedback=val['feedback'],
                suggestions=val.get('suggestions', []),
            )
            for key, val in report['criteria'].items()
        }

        response = ResumeAnalysisResponse(
            status=AnalysisStatus.success,
            overall_score=report['overall_score'],
            summary=report['summary'],
            criteria=criteria,
            top_strengths=report['top_strengths'],
            top_improvements=report['top_improvements'],
            file_name=file_name,
        )

        loop = asyncio.new_event_loop()
        try:
            record_id = loop.run_until_complete(_save_to_db(response))
        finally:
            loop.close()

        payload = {'record_id': record_id, **response.model_dump()}

        if callback_url:
            _send_webhook(callback_url, payload)

        return payload

    except Exception as exc:
        countdown = 20 if '429' in str(exc) else 10
        raise self.retry(exc=exc, countdown=countdown) from None


def _send_webhook(url: str, payload: dict) -> None:
    """Отправляет результат на callback URL с retry логикой."""
    import httpx

    for attempt in range(3):
        try:
            httpx.post(url, json=payload, timeout=10)
            return
        except Exception:
            if attempt == 2:
                print(f'[Webhook] Не удалось доставить на {url} после 3 попыток')
