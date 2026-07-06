"""Интеграционные тесты для экспорта в PDF."""

import json
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ResumeAnalysisModel
from app.main import app


async def test_export_to_pdf_success(
    session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Проверяет успешный экспорт анализа в PDF."""
    # Создаём тестовую запись в БД
    test_analysis = ResumeAnalysisModel(
        file_name='test_resume.pdf',
        overall_score=8,
        summary='Great resume with concrete achievements.',
        criteria={
            'skills': {
                'score': 9,
                'feedback': 'Strong technical skills.',
                'suggestions': ['Add proficiency levels'],
            },
            'experience': {
                'score': 8,
                'feedback': 'Good experience progression.',
                'suggestions': [],
            },
            'structure': {
                'score': 7,
                'feedback': 'Well structured.',
                'suggestions': ['Improve formatting'],
            },
            'language': {
                'score': 8,
                'feedback': 'Professional tone.',
                'suggestions': [],
            },
        },
        top_strengths=['Concrete metrics', 'Modern stack'],
        top_improvements=['Add summary'],
        created_at=datetime.now(),
    )

    session.add(test_analysis)
    await session.commit()
    await session.refresh(test_analysis)
    analysis_id = test_analysis.id_

    # Запрашиваем PDF экспорт
    response = await async_client.get(
        f'/api/v1/resume/{analysis_id}/export',
    )

    # Проверяем статус и формат
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'
    assert 'attachment' in response.headers['content-disposition']
    assert f'resume-analysis-{analysis_id}.pdf' in response.headers['content-disposition']

    # Проверяем что это валидный PDF
    assert response.content.startswith(b'%PDF')
    assert len(response.content) > 0


async def test_export_to_pdf_not_found(
    async_client: AsyncClient,
) -> None:
    """Проверяет что экспорт возвращает 404 для несуществующей записи."""
    response = await async_client.get('/api/v1/resume/99999/export')

    assert response.status_code == 404
