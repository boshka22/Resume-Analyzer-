"""Модуль эндпоинтов для анализа резюме."""

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.v1.resume import (
    ResumeAnalysisHistoryResponse,
    ResumeAnalysisResponse,
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
    summary='Анализ резюме',
    description='Принимает файл резюме в формате PDF или TXT и возвращает детальный анализ.',
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {'description': 'Успешный анализ резюме'},
        400: {'description': 'Некорректный файл или формат'},
        500: {'description': 'Внутренняя ошибка сервера'},
    },
)
async def analyze_resume(
    file: UploadFile = File(...),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeAnalysisResponse:
    """Анализирует загруженное резюме и сохраняет результат в БД.

    Args:
        file: Файл резюме в формате PDF или TXT. Максимальный размер 5MB.
        service: Экземпляр ResumeService из dependency injection.

    Returns:
        ResumeAnalysisResponse: Полный отчёт анализа резюме.
    """
    return await service.analyze(file=file)


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
