"""Модуль FastAPI приложения Resume Analyzer."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.resume import router as resume_router
from app.core.database import Base, engine

__all__ = [
    'app',
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Управляет жизненным циклом FastAPI приложения.

    Создаёт таблицы БД при старте если они не существуют.

    Args:
        app: Экземпляр FastAPI приложения.

    Yields:
        None: Передаёт управление приложению.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Resume Analyzer API запущен')
    yield
    print('Resume Analyzer API остановлен')


app = FastAPI(
    title='Resume Analyzer API',
    description='AI анализатор резюме на основе LangGraph',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(resume_router, prefix='/api/v1')


@app.get('/health', tags=['system'])
async def health() -> dict:
    """Проверяет работоспособность сервиса.

    Returns:
        dict: Статус сервиса.
    """
    return {'status': 'ok', 'service': 'Resume Analyzer'}


if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
    )
