"""Модуль конфигурации приложения."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

__all__ = [
    'settings',
]

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения.

    Attributes:
        groq_api_key: API ключ для доступа к Groq LLM.
        database_url: URL подключения к PostgreSQL.
        postgres_db: Имя базы данных PostgreSQL.
        postgres_user: Пользователь PostgreSQL.
        postgres_password: Пароль PostgreSQL.
        max_file_size_mb: Максимальный размер загружаемого файла в MB.
        model_name: Название используемой LLM модели.
        model_temperature: Температура модели для генерации ответов.
    """

    groq_api_key: str
    database_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    max_file_size_mb: int = 5
    model_name: str = 'llama-3.3-70b-versatile'
    model_temperature: float = 0.3

    class Config:
        env_file = '.env'


settings = Settings()
