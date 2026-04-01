"""Модуль узлов LangGraph графа анализа резюме."""

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, SecretStr

from app.core.config import settings
from app.graph.state import ResumeState

__all__ = [
    'analyze_skills',
    'analyze_experience',
    'analyze_structure',
    'analyze_language',
    'compile_report',
]


def _get_model() -> BaseChatModel:
    """Возвращает LLM модель в зависимости от настроенного провайдера.

    Returns:
        BaseChatModel: Инстанс языковой модели.

    Raises:
        ValueError: Если провайдер не поддерживается.
    """
    provider = settings.llm_provider.lower()

    if provider == 'groq':
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.model_name,
            temperature=settings.model_temperature,
            api_key=SecretStr(settings.groq_api_key),
        )

    if provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.model_name,
            temperature=settings.model_temperature,
            google_api_key=settings.google_api_key,
        )

    if provider == 'ollama':
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.model_name,
            temperature=settings.model_temperature,
            base_url=settings.ollama_base_url,
        )

    raise ValueError(f'Неизвестный LLM провайдер: {provider}. Доступны: groq, gemini, ollama')


_model = _get_model()


class _CriteriaResult(BaseModel):
    """Внутренняя схема результата анализа по одному критерию."""

    score: int = Field(description='Оценка от 1 до 10')
    feedback: str = Field(description='Краткий фидбек 1-2 предложения')
    suggestions: list[str] = Field(description='2-3 конкретных совета по улучшению')


def _analyze_criteria(
    resume_text: str,
    criteria: str,
    instructions: str,
) -> dict:
    """Универсальная функция анализа резюме по заданному критерию."""
    parser = JsonOutputParser(pydantic_object=_CriteriaResult)

    template = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                f"""Ты эксперт HR и карьерный консультант.
Анализируй резюме строго по критерию: {criteria}

{instructions}

Возвращай ТОЛЬКО JSON. score строго от 1 до 10.
{{format_instructions}}""",
            ),
            ('human', 'Резюме:\n\n{resume_text}'),
        ]
    )

    chain = template | _model | parser
    return chain.invoke(
        {
            'resume_text': resume_text,
            'format_instructions': parser.get_format_instructions(),
        }
    )


def analyze_skills(state: ResumeState) -> dict:
    """Анализирует навыки и технический стек в резюме."""
    print('[Агент навыков] Анализирую...')
    result = _analyze_criteria(
        state['resume_text'],
        'Навыки и технический стек',
        """Оцени:
- Релевантность указанных навыков
- Конкретность (версии, уровни владения)
- Баланс hard skills и soft skills
- Актуальность технологий""",
    )
    return {'skills_analysis': result, 'scores': [result['score']]}


def analyze_experience(state: ResumeState) -> dict:
    """Анализирует опыт работы в резюме."""
    print('[Агент опыта] Анализирую...')
    result = _analyze_criteria(
        state['resume_text'],
        'Опыт работы',
        """Оцени:
- Наличие конкретных достижений с цифрами
- Прогрессия карьеры
- Релевантность опыта
- Описание обязанностей (глаголы действия, конкретика)""",
    )
    return {'experience_analysis': result, 'scores': [result['score']]}


def analyze_structure(state: ResumeState) -> dict:
    """Анализирует структуру и оформление резюме."""
    print('[Агент структуры] Анализирую...')
    result = _analyze_criteria(
        state['resume_text'],
        'Структура и оформление',
        """Оцени:
- Наличие всех ключевых разделов (контакты, опыт, образование, навыки)
- Логичность порядка разделов
- Краткость и читаемость
- Наличие лишней информации""",
    )
    return {'structure_analysis': result, 'scores': [result['score']]}


def analyze_language(state: ResumeState) -> dict:
    """Анализирует язык и подачу информации в резюме."""
    print('[Агент языка] Анализирую...')
    result = _analyze_criteria(
        state['resume_text'],
        'Язык и подача',
        """Оцени:
- Грамотность и стиль
- Использование сильных глаголов действия
- Отсутствие клише и водянистых фраз
- Профессиональный тон""",
    )
    return {'language_analysis': result, 'scores': [result['score']]}


def compile_report(state: ResumeState) -> dict:
    """Собирает итоговый отчёт на основе результатов всех агентов."""
    print('[Финальный агент] Составляю отчёт...')

    scores = state['scores']
    overall = round(sum(scores) / len(scores))

    criteria_map = {
        'skills': state['skills_analysis'],
        'experience': state['experience_analysis'],
        'structure': state['structure_analysis'],
        'language': state['language_analysis'],
    }

    parser = JsonOutputParser()
    template = ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """Ты карьерный консультант. Составь итоговый отчёт на основе анализа резюме.
Верни ТОЛЬКО JSON:
{{
    "summary": "общее впечатление 2-3 предложения",
    "top_strengths": ["сильная сторона 1", "сильная сторона 2", "сильная сторона 3"],
    "top_improvements": ["улучшение 1", "улучшение 2", "улучшение 3"]
}}""",
            ),
            (
                'human',
                """Результаты анализа:
Навыки (оценка {skills_score}/10): {skills_feedback}
Опыт (оценка {experience_score}/10): {experience_feedback}
Структура (оценка {structure_score}/10): {structure_feedback}
Язык (оценка {language_score}/10): {language_feedback}
Общая оценка: {overall}/10""",
            ),
        ]
    )

    chain = template | _model | parser
    summary = chain.invoke(
        {
            'skills_score': state['skills_analysis']['score'],
            'skills_feedback': state['skills_analysis']['feedback'],
            'experience_score': state['experience_analysis']['score'],
            'experience_feedback': state['experience_analysis']['feedback'],
            'structure_score': state['structure_analysis']['score'],
            'structure_feedback': state['structure_analysis']['feedback'],
            'language_score': state['language_analysis']['score'],
            'language_feedback': state['language_analysis']['feedback'],
            'overall': overall,
        }
    )

    return {
        'final_report': {
            'overall_score': overall,
            'summary': summary.get('summary', ''),
            'criteria': criteria_map,
            'top_strengths': summary.get('top_strengths', []),
            'top_improvements': summary.get('top_improvements', []),
        },
    }
