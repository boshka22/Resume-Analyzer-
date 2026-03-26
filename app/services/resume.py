"""Модуль сервисного слоя для анализа резюме."""

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.builder import build_resume_graph
from app.parsers.file import extract_text
from app.repositories.resume import ResumeRepository
from app.schemas.v1.resume import (
    AnalysisStatus,
    CriteriaScore,
    ResumeAnalysisHistoryItem,
    ResumeAnalysisHistoryResponse,
    ResumeAnalysisResponse,
)

__all__ = [
    'ResumeService',
]

_graph = build_resume_graph()

MIN_RESUME_LENGTH = 100


class ResumeService:
    """Сервис анализа резюме.

    Отвечает за оркестрацию парсинга файла, запуск графа,
    сохранение результата в БД и формирование ответа.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис с сессией базы данных.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """
        self._repo = ResumeRepository(session=session)

    async def analyze(self, file: UploadFile) -> ResumeAnalysisResponse:
        """Анализирует загруженный файл резюме и сохраняет результат в БД.

        Args:
            file: Загруженный файл резюме в формате PDF или TXT.

        Raises:
            HTTPException: 400 — если резюме слишком короткое.
            HTTPException: 500 — если произошла ошибка при анализе.

        Returns:
            ResumeAnalysisResponse: Полный отчёт анализа резюме.
        """
        resume_text = await extract_text(file)

        if len(resume_text) < MIN_RESUME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Резюме слишком короткое. Минимум {MIN_RESUME_LENGTH} символов.',
            )

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
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ошибка анализа: {str(e)}',
            ) from e

        response = self._build_response(
            result=result,
            file_name=file.filename,
        )

        await self._repo.create(response=response)

        return response

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

    def _build_response(
        self,
        result: dict,
        file_name: str | None,
    ) -> ResumeAnalysisResponse:
        """Формирует Pydantic ответ из результата графа.

        Args:
            result: Результат выполнения LangGraph графа.
            file_name: Имя загруженного файла.

        Returns:
            ResumeAnalysisResponse: Структурированный ответ API.
        """
        report = result['final_report']

        criteria = {
            key: CriteriaScore(
                score=val['score'],
                feedback=val['feedback'],
                suggestions=val.get('suggestions', []),
            )
            for key, val in report['criteria'].items()
        }

        return ResumeAnalysisResponse(
            status=AnalysisStatus.success,
            overall_score=report['overall_score'],
            summary=report['summary'],
            criteria=criteria,
            top_strengths=report['top_strengths'],
            top_improvements=report['top_improvements'],
            file_name=file_name,
        )
