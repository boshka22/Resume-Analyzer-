"""Модуль эндпоинтов для анализа резюме."""

from fastapi import APIRouter, Depends, File, Form, Path, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.v1.resume import (
    AnalyzeTaskResponse,
    ResumeAnalysisHistoryResponse,
    ResumeAnalysisResponse,
    TaskStatusResponse,
)
from app.services.resume import ResumeService

__all__ = [
    'router',
]

router = APIRouter(
    prefix='/resume',
    tags=['resume'],
)


def get_resume_service(
    session: AsyncSession = Depends(get_session),
) -> ResumeService:
    """Возвращает экземпляр ResumeService с сессией БД.

    Args:
        session: Асинхронная сессия SQLAlchemy из dependency injection.

    Returns:
        ResumeService: Экземпляр сервиса анализа резюме.
    """
    return ResumeService(session=session)


@router.post(
    path='/analyze',
    summary='Запустить анализ резюме',
    description='Принимает файл, ставит задачу в очередь. Возвращает task_id немедленно. '
    'Если резюме уже анализировалось — возвращает результат из кэша мгновенно.',
    response_model=AnalyzeTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {'description': 'Задача принята в обработку или результат из кэша'},
        400: {'description': 'Некорректный файл или формат'},
    },
)
async def analyze_resume(
    response: Response,
    file: UploadFile = File(...),
    callback_url: str | None = Form(default=None),
    service: ResumeService = Depends(get_resume_service),
) -> AnalyzeTaskResponse:
    """Принимает файл резюме и ставит задачу анализа в очередь Celery.

    Перед постановкой в очередь проверяет кэш Redis. Если результат найден —
    возвращает его мгновенно с заголовком X-Cache: HIT и полем cached=true.
    Если кэша нет — ставит задачу в Celery и возвращает task_id для поллинга.

    Args:
        response: Объект HTTP ответа для установки заголовков.
        file: Файл резюме в формате PDF или TXT. Максимальный размер 5MB.
        callback_url: Опциональный URL для webhook уведомления о завершении анализа.
        service: Экземпляр ResumeService из dependency injection.

    Returns:
        AnalyzeTaskResponse: ID таска и статус pending, либо результат из кэша.
    """
    result = await service.analyze(file=file, callback_url=callback_url)
    response.headers['X-Cache'] = 'HIT' if result.cached else 'MISS'
    return result


@router.get(
    path='/analyze/{task_id}/status',
    summary='Статус анализа',
    description='Возвращает текущий статус задачи и результат если анализ завершён.',
    response_model=TaskStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {'description': 'Статус задачи'},
    },
)
async def get_task_status(
    task_id: str = Path(...),
    service: ResumeService = Depends(get_resume_service),
) -> TaskStatusResponse:
    """Поллинг статуса задачи анализа резюме.

    Args:
        task_id: ID Celery таска полученный из POST /analyze.
        service: Экземпляр ResumeService из dependency injection.

    Returns:
        TaskStatusResponse: Статус и результат если готов.
    """
    return await service.get_task_status(task_id=task_id)


@router.get(
    path='/history',
    summary='История анализов',
    description='Возвращает список всех выполненных анализов резюме.',
    response_model=ResumeAnalysisHistoryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {'description': 'Список истории анализов'},
    },
)
async def get_history(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeAnalysisHistoryResponse:
    """Возвращает историю анализов резюме с пагинацией.

    Args:
        limit: Максимальное количество записей. По умолчанию 10.
        offset: Смещение от начала списка. По умолчанию 0.
        service: Экземпляр ResumeService из dependency injection.

    Returns:
        ResumeAnalysisHistoryResponse: Список записей истории.
    """
    return await service.get_history(limit=limit, offset=offset)


@router.get(
    path='/{id}',
    summary='Получение анализа по ID',
    description='Возвращает результат анализа резюме по идентификатору.',
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {'description': 'Результат анализа резюме'},
        404: {'description': 'Анализ не найден'},
    },
)
async def get_by_id(
    id_: int = Path(alias='id', ge=1),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeAnalysisResponse:
    """Возвращает результат анализа резюме по идентификатору.

    Args:
        id_: Идентификатор записи анализа.
        service: Экземпляр ResumeService из dependency injection.

    Returns:
        ResumeAnalysisResponse: Полный отчёт анализа резюме.
    """
    return await service.get_by_id(id_=id_)
