"""Модуль Pydantic схем для эндпоинтов анализа резюме."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

__all__ = [
    'AnalysisStatus',
    'CriteriaScore',
    'ResumeAnalysisResponse',
    'ResumeAnalysisHistoryItem',
    'ResumeAnalysisHistoryResponse',
]


class AnalysisStatus(StrEnum):
    """Статус выполнения анализа резюме."""

    success = 'success'
    error = 'error'


class CriteriaScore(BaseModel):
    """Результат анализа по одному критерию.

    Attributes:
        score: Оценка от 1 до 10.
        feedback: Краткий фидбек по критерию.
        suggestions: Список конкретных советов по улучшению.
    """

    score: int = Field(ge=1, le=10, description='Оценка от 1 до 10')
    feedback: str = Field(description='Краткий фидбек 1-2 предложения')
    suggestions: list[str] = Field(description='Конкретные советы по улучшению')


class ResumeAnalysisResponse(BaseModel):
    """Полный отчёт анализа резюме.

    Attributes:
        status: Статус выполнения анализа.
        overall_score: Итоговая оценка резюме от 1 до 10.
        summary: Общее впечатление от резюме.
        criteria: Результаты анализа по каждому критерию.
        top_strengths: Топ-3 сильных стороны резюме.
        top_improvements: Топ-3 приоритетных улучшения.
        file_name: Имя загруженного файла.
    """

    status: AnalysisStatus
    overall_score: int = Field(ge=1, le=10)
    summary: str
    criteria: dict[str, CriteriaScore]
    top_strengths: list[str]
    top_improvements: list[str]
    file_name: str | None = None


class ResumeAnalysisHistoryItem(BaseModel):
    """Элемент истории анализа резюме.

    Attributes:
        id_: Идентификатор записи.
        file_name: Имя загруженного файла.
        overall_score: Итоговая оценка резюме.
        summary: Общее впечатление от резюме.
        created_at: Дата и время создания записи.
    """

    id_: int
    file_name: str | None = None
    overall_score: int
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeAnalysisHistoryResponse(BaseModel):
    """Ответ со списком истории анализов.

    Attributes:
        items: Список записей истории.
        total: Общее количество записей.
    """

    items: list[ResumeAnalysisHistoryItem]
    total: int
