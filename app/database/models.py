"""Модуль моделей базы данных."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

__all__ = [
    'ResumeAnalysisModel',
]


class ResumeAnalysisModel(Base):
    """Модель таблицы результатов анализа резюме.

    Attributes:
        id_: Первичный ключ.
        file_name: Имя загруженного файла.
        overall_score: Итоговая оценка резюме от 1 до 10.
        summary: Общее впечатление от резюме.
        criteria: JSON с результатами анализа по критериям.
        top_strengths: JSON со списком сильных сторон.
        top_improvements: JSON со списком улучшений.
        created_at: Дата и время создания записи.
    """

    __tablename__ = 'resume_analyses'

    id_: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False)
    top_strengths: Mapped[list] = mapped_column(JSON, nullable=False)
    top_improvements: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
