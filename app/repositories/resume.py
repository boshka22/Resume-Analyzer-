"""Модуль репозитория для работы с результатами анализа резюме."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ResumeAnalysisModel
from app.schemas.v1.resume import ResumeAnalysisResponse

__all__ = [
    'ResumeRepository',
]


class ResumeRepository:
    """Репозиторий для записи и получения результатов анализа резюме."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий с сессией базы данных.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """
        self._session = session

    async def create(
        self,
        response: ResumeAnalysisResponse,
    ) -> ResumeAnalysisModel:
        """Сохраняет результат анализа резюме в базу данных.

        Args:
            response: Pydantic схема с результатом анализа.

        Returns:
            ResumeAnalysisModel: Созданная запись в базе данных.
        """
        model = ResumeAnalysisModel(
            file_name=response.file_name,
            overall_score=response.overall_score,
            summary=response.summary,
            criteria={key: val.model_dump() for key, val in response.criteria.items()},
            top_strengths=response.top_strengths,
            top_improvements=response.top_improvements,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def get_by_id(self, id_: int) -> ResumeAnalysisModel | None:
        """Возвращает результат анализа по идентификатору.

        Args:
            id_: Идентификатор записи.

        Returns:
            ResumeAnalysisModel | None: Найденная запись или None.
        """
        query = select(ResumeAnalysisModel).where(
            ResumeAnalysisModel.id_ == id_,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ResumeAnalysisModel]:
        """Возвращает список результатов анализа с пагинацией.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение от начала списка.

        Returns:
            list[ResumeAnalysisModel]: Список записей.
        """
        query = (
            select(ResumeAnalysisModel)
            .order_by(ResumeAnalysisModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
