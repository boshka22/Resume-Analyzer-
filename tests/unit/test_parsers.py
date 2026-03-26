"""Юнит тесты для модуля парсинга файлов."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.parsers.file import _parse_txt, extract_text

__all__: list[str] = []


def test_parse_txt_utf8() -> None:
    """Проверяет успешное декодирование UTF-8 текста."""
    content = 'Привет мир'.encode()
    result = _parse_txt(content)
    assert result == 'Привет мир'


def test_parse_txt_cp1251() -> None:
    """Проверяет успешное декодирование CP1251 текста."""
    content = 'Привет мир'.encode('cp1251')
    result = _parse_txt(content)
    assert result == 'Привет мир'


def test_parse_txt_empty_raises() -> None:
    """Проверяет что пустой файл вызывает HTTPException 400."""
    with pytest.raises(HTTPException) as exc:
        _parse_txt(b'   ')
    assert exc.value.status_code == 400


def test_parse_txt_strips_whitespace() -> None:
    """Проверяет что пробелы в начале и конце обрезаются."""
    content = '  текст резюме  '.encode()
    result = _parse_txt(content)
    assert result == 'текст резюме'


@pytest.mark.asyncio
async def test_extract_text_unsupported_format() -> None:
    """Проверяет что неподдерживаемый формат вызывает HTTPException 400."""
    mock_file = AsyncMock()
    mock_file.filename = 'resume.docx'
    mock_file.read = AsyncMock(return_value=b'content')

    with pytest.raises(HTTPException) as exc:
        await extract_text(mock_file)
    assert exc.value.status_code == 400
    assert 'PDF' in exc.value.detail


@pytest.mark.asyncio
async def test_extract_text_too_large() -> None:
    """Проверяет что файл больше 5MB вызывает HTTPException 400."""
    mock_file = AsyncMock()
    mock_file.filename = 'resume.txt'
    mock_file.read = AsyncMock(return_value=b'x' * (6 * 1024 * 1024))

    with pytest.raises(HTTPException) as exc:
        await extract_text(mock_file)
    assert exc.value.status_code == 400
    assert '5MB' in exc.value.detail
