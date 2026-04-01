"""Модуль кэширования результатов анализа резюме."""

import hashlib
import json

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.v1.resume import ResumeAnalysisResponse

__all__ = ['ResumeCache']

CACHE_TTL = 60 * 60 * 24
CACHE_PREFIX = 'resume:analysis'


def _make_key(resume_text: str) -> str:
    """Генерирует ключ кэша на основе MD5 хэша текста резюме.

    Args:
        resume_text: Текст резюме.

    Returns:
        str: Ключ для Redis.
    """
    text_hash = hashlib.md5(resume_text.encode()).hexdigest()
    return f'{CACHE_PREFIX}:{text_hash}'


class ResumeCache:
    """Кэш результатов анализа резюме в Redis."""

    def __init__(self) -> None:
        self._redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def get(self, resume_text: str) -> ResumeAnalysisResponse | None:
        """Возвращает закэшированный результат или None если кэша нет.

        Args:
            resume_text: Текст резюме.

        Returns:
            ResumeAnalysisResponse | None: Результат из кэша или None.
        """
        key = _make_key(resume_text)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return ResumeAnalysisResponse.model_validate(json.loads(raw))

    async def set(self, resume_text: str, response: ResumeAnalysisResponse) -> None:
        """Сохраняет результат анализа в кэш.

        Args:
            resume_text: Текст резюме (используется как ключ).
            response: Результат анализа для кэширования.
        """
        key = _make_key(resume_text)
        await self._redis.setex(
            name=key,
            time=CACHE_TTL,
            value=response.model_dump_json(),
        )

    async def close(self) -> None:
        """Закрывает соединение с Redis."""
        await self._redis.close()
