"""Тесты для генератора PDF."""

from app.pdf.generator import PDFGenerator
from app.schemas.v1.resume import CriteriaScore, ResumeAnalysisResponse, AnalysisStatus


def test_pdf_generator_creates_valid_pdf() -> None:
    """Проверяет что генератор создаёт валидный PDF."""
    analysis = ResumeAnalysisResponse(
        status=AnalysisStatus.success,
        overall_score=8,
        summary='Great resume with concrete achievements and modern tech stack.',
        criteria={
            'skills': CriteriaScore(
                score=9,
                feedback='Strong technical skills with good coverage.',
                suggestions=['Add proficiency levels', 'Include specific versions'],
            ),
            'experience': CriteriaScore(
                score=8,
                feedback='Good experience progression with metrics.',
                suggestions=['Add GitHub links', 'Describe team collaboration'],
            ),
            'structure': CriteriaScore(
                score=7,
                feedback='Well structured but some redundancy.',
                suggestions=['Remove duplicate contacts', 'Add summary section'],
            ),
            'language': CriteriaScore(
                score=8,
                feedback='Professional tone with strong action verbs.',
                suggestions=['Remove clichés', 'Shorten long sentences'],
            ),
        },
        top_strengths=['Concrete metrics', 'Modern stack', 'Career progression'],
        top_improvements=['Add summary', 'Specify skill levels'],
        file_name='test_resume.pdf',
    )

    generator = PDFGenerator()
    pdf_bytes = generator.generate(analysis)

    # Проверяем что PDF не пустой и начинается с PDF сигнатуры
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')


def test_pdf_generator_with_different_scores() -> None:
    """Проверяет генерацию PDF с разными оценками."""
    for score in [1, 5, 10]:
        analysis = ResumeAnalysisResponse(
            status=AnalysisStatus.success,
            overall_score=score,
            summary=f'Test summary for score {score}.',
            criteria={
                'skills': CriteriaScore(
                    score=score,
                    feedback='Test feedback',
                    suggestions=['Test suggestion'],
                ),
                'experience': CriteriaScore(
                    score=score,
                    feedback='Test feedback',
                    suggestions=[],
                ),
                'structure': CriteriaScore(
                    score=score,
                    feedback='Test feedback',
                    suggestions=['Suggestion 1', 'Suggestion 2'],
                ),
                'language': CriteriaScore(
                    score=score,
                    feedback='Test feedback',
                    suggestions=[],
                ),
            },
            top_strengths=['Strength 1'],
            top_improvements=['Improvement 1'],
            file_name='test.pdf',
        )

        generator = PDFGenerator()
        pdf_bytes = generator.generate(analysis)

        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
