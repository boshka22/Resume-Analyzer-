"""Модуль состояния LangGraph графа анализа резюме."""

import operator
from typing import Annotated, TypedDict

__all__ = [
    'ResumeState',
]


class ResumeState(TypedDict):
    """Состояние графа анализа резюме.

    Attributes:
        resume_text: Текст резюме для анализа.
        skills_analysis: Результат анализа навыков.
        experience_analysis: Результат анализа опыта работы.
        structure_analysis: Результат анализа структуры.
        language_analysis: Результат анализа языка и подачи.
        scores: Список оценок от всех агентов — суммируется автоматически.
        final_report: Итоговый отчёт с рекомендациями.
    """

    resume_text: str
    skills_analysis: dict
    experience_analysis: dict
    structure_analysis: dict
    language_analysis: dict
    scores: Annotated[list, operator.add]
    final_report: dict
