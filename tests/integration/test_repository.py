"""Интеграционные тесты для репозитория анализа резюме."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.resume import ResumeRepository
from app.schemas.v1.resume import (
    AnalysisStatus,
    CriteriaScore,
    ResumeAnalysisResponse,
)

__all__: list[str] = []

MOCK_RESPONSE = ResumeAnalysisResponse(
    status=AnalysisStatus.success,
    overall_score=8,
    summary='Хорошее резюме.',
    criteria={
        'skills': CriteriaScore(
            score=8,
            feedback='Хороший стек.',
            suggestions=['Добавить уровни владения'],
        ),
        'experience': CriteriaScore(
            score=9,
            feedback='Отличные достижения.',
            suggestions=['Больше метрик'],
        ),
        'structure': CriteriaScore(
            score=7,
            feedback='Структура понятная.',
            suggestions=['Добавить summary'],
        ),
        'language': CriteriaScore(
            score=8,
            feedback='Профессиональный тон.',
            suggestions=['Убрать клише'],
        ),
    },
    top_strengths=['Метрики', 'Стек', 'Прогрессия'],
    top_improvements=['Summary', 'Клише', 'Уровни'],
    file_name='test_resume.pdf',
)


@pytest.mark.asyncio
async def test_create_analysis(session: AsyncSession) -> None:
    """Проверяет успешное создание записи анализа в БД."""
    repo = ResumeRepository(session=session)

    model = await repo.create(response=MOCK_RESPONSE)

    assert model.id_ is not None
    assert model.overall_score == 8
    assert model.file_name == 'test_resume.pdf'
    assert model.summary == 'Хорошее резюме.'


@pytest.mark.asyncio
async def test_get_by_id(session: AsyncSession) -> None:
    """Проверяет получение записи анализа по идентификатору."""
    repo = ResumeRepository(session=session)

    created = await repo.create(response=MOCK_RESPONSE)
    found = await repo.get_by_id(id_=created.id_)

    assert found is not None
    assert found.id_ == created.id_
    assert found.overall_score == created.overall_score


@pytest.mark.asyncio
async def test_get_by_id_not_found(session: AsyncSession) -> None:
    """Проверяет что несуществующий ID возвращает None."""
    repo = ResumeRepository(session=session)

    result = await repo.get_by_id(id_=99999)

    assert result is None


@pytest.mark.asyncio
async def test_get_all(session: AsyncSession) -> None:
    """Проверяет получение списка анализов с пагинацией."""
    repo = ResumeRepository(session=session)

    await repo.create(response=MOCK_RESPONSE)
    await repo.create(response=MOCK_RESPONSE)

    items = await repo.get_all(limit=10, offset=0)

    assert len(items) >= 2


@pytest.mark.asyncio
async def test_get_all_with_limit(session: AsyncSession) -> None:
    """Проверяет что limit корректно ограничивает количество записей."""
    repo = ResumeRepository(session=session)

    for _ in range(5):
        await repo.create(response=MOCK_RESPONSE)

    items = await repo.get_all(limit=2, offset=0)

    assert len(items) == 2
