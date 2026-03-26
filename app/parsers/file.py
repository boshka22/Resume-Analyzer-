"""Модуль для извлечения текста из загружаемых файлов резюме."""

import io

from fastapi import HTTPException, UploadFile
from PyPDF2 import PdfReader

__all__ = [
    'extract_text',
]

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


async def extract_text(file: UploadFile) -> str:
    """Извлекает текст из загруженного файла PDF или TXT.

    Args:
        file: Загруженный файл резюме в формате PDF или TXT.

    Raises:
        HTTPException: 400 — если файл превышает 5MB.
        HTTPException: 400 — если формат файла не поддерживается.
        HTTPException: 400 — если файл пустой.

    Returns:
        str: Извлечённый текст резюме.
    """
    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail='Файл слишком большой. Максимум 5MB.',
        )

    filename = (file.filename or '').lower()

    if filename.endswith('.pdf'):
        return _parse_pdf(content)
    elif filename.endswith('.txt'):
        return _parse_txt(content)

    raise HTTPException(
        status_code=400,
        detail='Поддерживаются только PDF и TXT файлы.',
    )


def _parse_pdf(content: bytes) -> str:
    """Извлекает текст из PDF файла.

    Args:
        content: Байтовое содержимое PDF файла.

    Raises:
        HTTPException: 400 — если текст не удалось извлечь или файл повреждён.

    Returns:
        str: Извлечённый текст из всех страниц PDF.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail='Не удалось извлечь текст из PDF. Возможно файл отсканирован.',
            )
        return text.strip()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Ошибка чтения PDF: {str(e)}',
        ) from e


def _parse_txt(content: bytes) -> str:
    """Извлекает текст из TXT файла.

    Пробует декодировать сначала в UTF-8, затем в CP1251.

    Args:
        content: Байтовое содержимое TXT файла.

    Raises:
        HTTPException: 400 — если не удалось декодировать файл.
        HTTPException: 400 — если файл пустой.

    Returns:
        str: Декодированный текст файла.
    """
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = content.decode('cp1251')
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail='Не удалось прочитать файл. Используй UTF-8 или CP1251.',
            ) from e

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail='Файл пустой.',
        )

    return text.strip()
