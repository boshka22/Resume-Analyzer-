"""Интеграционные тесты для эндпоинтов Resume Analyzer API."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.v1.resume import (
    AnalysisStatus,
    CriteriaScore,
    ResumeAnalysisResponse,
)

__all__: list[str] = []

MOCK_RESPONSE = ResumeAnalysisResponse(
    status=AnalysisStatus.success,
    overall_score=8,
    summary='Хорошее резюме с конкретными достижениями.',
    criteria={
        'skills': CriteriaScore(
            score=8,
            feedback='Хороший стек.',
            suggestions=['Добавить уровни владения'],
        ),
        'experience': CriteriaScore(
            score=9,
            feedback='Отличные достижения с цифрами.',
            suggestions=['Добавить больше метрик'],
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
    top_strengths=['Конкретные метрики', 'Современный стек', 'Прогрессия'],
    top_improvements=['Добавить summary', 'Убрать клише', 'Уровни навыков'],
    file_name='resume.txt',
)


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """Проверяет что health эндпоинт возвращает 200."""
    response = await client.get('/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


@pytest.mark.asyncio
async def test_analyze_resume_success(client: AsyncClient) -> None:
    """Проверяет успешный анализ TXT резюме с сохранением в БД."""
    with patch(
        'app.services.resume.ResumeService.analyze',
        new_callable=AsyncMock,
        return_value=MOCK_RESPONSE,
    ):
        response = await client.post(
            '/api/v1/resume/analyze',
            files={
                'file': ('resume.txt', b'Some resume text ' * 20, 'text/plain'),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert data['overall_score'] == 8
    assert 'criteria' in data


@pytest.mark.asyncio
async def test_analyze_resume_wrong_format(client: AsyncClient) -> None:
    """Проверяет что неподдерживаемый формат возвращает 400."""
    response = await client.post(
        '/api/v1/resume/analyze',
        files={
            'file': ('resume.docx', b'content', 'application/octet-stream'),
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_history_empty(client: AsyncClient) -> None:
    """Проверяет что история возвращает пустой список если анализов нет."""
    response = await client.get('/api/v1/resume/history')

    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert isinstance(data['items'], list)


@pytest.mark.asyncio
async def test_get_by_id_not_found(client: AsyncClient) -> None:
    """Проверяет что несуществующий ID возвращает 404."""
    response = await client.get('/api/v1/resume/99999')

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_history_pagination(client: AsyncClient) -> None:
    """Проверяет параметры пагинации истории."""
    response = await client.get('/api/v1/resume/history?limit=5&offset=0')

    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) <= 5
