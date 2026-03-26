"""Модуль сборки LangGraph графа анализа резюме."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    analyze_experience,
    analyze_language,
    analyze_skills,
    analyze_structure,
    compile_report,
)
from app.graph.state import ResumeState

__all__ = [
    'build_resume_graph',
]


def build_resume_graph() -> Any:
    """Строит и компилирует LangGraph граф анализа резюме.

    Граф запускает четыре агента параллельно — навыки, опыт, структура, язык.
    После завершения всех агентов compile_report собирает итоговый отчёт.

    Returns:
        Скомпилированный граф готовый к вызову через invoke().
    """
    graph = StateGraph(ResumeState)

    graph.add_node('analyze_skills', analyze_skills)
    graph.add_node('analyze_experience', analyze_experience)
    graph.add_node('analyze_structure', analyze_structure)
    graph.add_node('analyze_language', analyze_language)
    graph.add_node('compile_report', compile_report)

    graph.add_edge(START, 'analyze_skills')
    graph.add_edge(START, 'analyze_experience')
    graph.add_edge(START, 'analyze_structure')
    graph.add_edge(START, 'analyze_language')

    graph.add_edge('analyze_skills', 'compile_report')
    graph.add_edge('analyze_experience', 'compile_report')
    graph.add_edge('analyze_structure', 'compile_report')
    graph.add_edge('analyze_language', 'compile_report')

    graph.add_edge('compile_report', END)

    return graph.compile()
