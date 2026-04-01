"""Модуль конфигурации приложения."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

__all__ = ['settings']

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    llm_provider: str = 'ollama'
    model_name: str = 'llama3.2'
    model_temperature: float = 0.3

    groq_api_key: str = ''
    google_api_key: str = ''
    ollama_base_url: str = 'http://host.docker.internal:11434'

    database_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    redis_url: str

    max_file_size_mb: int = 5

    class Config:
        env_file = '.env'


settings = Settings()
