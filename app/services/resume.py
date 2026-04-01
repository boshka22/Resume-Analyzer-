"""Модуль сервисного слоя для анализа резюме."""

from celery.result import AsyncResult
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.resume import ResumeCache
from app.celery_app import celery_app
from app.parsers.file import extract_text
from app.repositories.resume import ResumeRepository
from app.schemas.v1.resume import (
    AnalysisStatus,
    AnalyzeTaskResponse,
    CriteriaScore,
    ResumeAnalysisHistoryItem,
    ResumeAnalysisHistoryResponse,
    ResumeAnalysisResponse,
    TaskStatus,
    TaskStatusResponse,
)
from app.tasks.analyze import analyze_resume_task

__all__ = [
    'ResumeService',
]

MIN_RESUME_LENGTH = 100


class ResumeService:
    """Сервис анализа резюме.

    Отвечает за оркестрацию парсинга файла, постановку задачи в очередь,
    получение статуса и формирование ответа.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис с сессией базы данных.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """
        self._repo = ResumeRepository(session=session)

    async def analyze(
        self,
        file: UploadFile,
        callback_url: str | None = None,
    ) -> AnalyzeTaskResponse:
        """Принимает файл, ставит таск в очередь, возвращает task_id мгновенно.

        Args:
            file: Загруженный файл резюме в формате PDF или TXT.
            callback_url: URL для webhook
        Raises:
            HTTPException: 400 — если резюме слишком короткое.

        Returns:
            AnalyzeTaskResponse: ID таска и статус pending.
        """
        resume_text = await extract_text(file)

        if len(resume_text) < MIN_RESUME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Резюме слишком короткое. Минимум {MIN_RESUME_LENGTH} символов.',
            )

        cache = ResumeCache()
        try:
            cached_result = await cache.get(resume_text)
        finally:
            await cache.close()

        if cached_result is not None:
            return AnalyzeTaskResponse(
                task_id='cached',
                status=TaskStatus.success,
                cached=True,
                result=cached_result,
            )

        task = analyze_resume_task.delay(
            resume_text=resume_text,
            file_name=file.filename,
            callback_url=callback_url,
        )

        return AnalyzeTaskResponse(
            task_id=task.id,
            status=TaskStatus.pending,
        )

    async def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """Читает статус таска из Redis через Celery backend.

        Args:
            task_id: ID Celery таска.

        Returns:
            TaskStatusResponse: Статус и результат если готов.
        """
        task_result = AsyncResult(task_id, app=celery_app)
        raw_status = task_result.status.lower()

        try:
            task_status = TaskStatus(raw_status)
        except ValueError:
            task_status = TaskStatus.pending

        result = None
        if task_status == TaskStatus.success and task_result.result:
            raw = task_result.result
            criteria = {key: CriteriaScore(**val) for key, val in raw['criteria'].items()}
            result = ResumeAnalysisResponse(
                status=AnalysisStatus.success,
                overall_score=raw['overall_score'],
                summary=raw['summary'],
                criteria=criteria,
                top_strengths=raw['top_strengths'],
                top_improvements=raw['top_improvements'],
                file_name=raw.get('file_name'),
            )

        return TaskStatusResponse(
            task_id=task_id,
            status=task_status,
            result=result,
        )

    async def get_history(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> ResumeAnalysisHistoryResponse:
        """Возвращает историю анализов резюме с пагинацией.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение от начала списка.

        Returns:
            ResumeAnalysisHistoryResponse: Список записей истории.
        """
        items = await self._repo.get_all(limit=limit, offset=offset)

        return ResumeAnalysisHistoryResponse(
            items=[
                ResumeAnalysisHistoryItem(
                    id_=item.id_,
                    file_name=item.file_name,
                    overall_score=item.overall_score,
                    summary=item.summary,
                    created_at=item.created_at,
                )
                for item in items
            ],
            total=len(items),
        )

    async def get_by_id(self, id_: int) -> ResumeAnalysisResponse:
        """Возвращает результат анализа по идентификатору.

        Args:
            id_: Идентификатор записи.

        Raises:
            HTTPException: 404 — если запись не найдена.

        Returns:
            ResumeAnalysisResponse: Полный отчёт анализа резюме.
        """
        model = await self._repo.get_by_id(id_=id_)

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Анализ с ID {id_} не найден.',
            )

        criteria = {
            key: CriteriaScore(
                score=val['score'],
                feedback=val['feedback'],
                suggestions=val.get('suggestions', []),
            )
            for key, val in model.criteria.items()
        }

        return ResumeAnalysisResponse(
            status=AnalysisStatus.success,
            overall_score=model.overall_score,
            summary=model.summary,
            criteria=criteria,
            top_strengths=model.top_strengths,
            top_improvements=model.top_improvements,
            file_name=model.file_name,
        )
