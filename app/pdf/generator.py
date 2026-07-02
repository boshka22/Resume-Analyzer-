"""Генератор PDF отчётов анализа резюме."""

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
    Flowable,
)

from app.schemas.v1.resume import ResumeAnalysisResponse

__all__ = ['PDFGenerator']


class ProgressBar(Flowable):
    """Кастомный Flowable для отображения прогресс-бара."""

    def __init__(
        self,
        score: int,
        width: float = 150,
        height: float = 20,
        color: colors.Color | None = None,
    ) -> None:
        """Инициализирует прогресс-бар.

        Args:
            score: Оценка от 1 до 10.
            width: Ширина бара.
            height: Высота бара.
            color: Цвет заполнения.
        """
        super().__init__()
        self.score = score
        self.width = width
        self.height = height
        self.color = color or colors.HexColor('#17a2b8')

    def draw(self) -> None:
        """Рисует прогресс-бар на canvas."""
        canvas = self.canv
        filled_width = (self.score / 10) * self.width

        # Фон (пустой бар)
        canvas.setFillColor(colors.HexColor('#e9ecef'))
        canvas.rect(0, 0, self.width, self.height, fill=1)

        # Заполненная часть
        canvas.setFillColor(self.color)
        canvas.rect(0, 0, filled_width, self.height, fill=1)

        # Граница
        canvas.setStrokeColor(colors.HexColor('#dee2e6'))
        canvas.rect(0, 0, self.width, self.height, fill=0)


class PDFGenerator:
    """Генератор PDF отчётов анализа резюме."""

    # Цветовая схема
    COLOR_PRIMARY = colors.HexColor('#1a5490')
    COLOR_ACCENT = colors.HexColor('#17a2b8')
    COLOR_SUCCESS = colors.HexColor('#28a745')
    COLOR_WARNING = colors.HexColor('#ffc107')
    COLOR_DANGER = colors.HexColor('#dc3545')
    COLOR_LIGHT = colors.HexColor('#f8f9fa')
    COLOR_BORDER = colors.HexColor('#dee2e6')

    def __init__(self) -> None:
        """Инициализирует генератор."""
        self.width, self.height = A4

    def generate(self, analysis: ResumeAnalysisResponse) -> bytes:
        """Генерирует PDF отчёт из результатов анализа.

        Args:
            analysis: Результаты анализа резюме.

        Returns:
            PDF в виде байтов.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []
        styles = getSampleStyleSheet()

        # Заголовок
        story.extend(self._build_header(analysis, styles))
        story.append(Spacer(1, 0.5 * cm))

        # Общая оценка
        story.extend(self._build_overall_score(analysis, styles))
        story.append(Spacer(1, 0.5 * cm))

        # Резюме
        story.extend(self._build_summary(analysis, styles))
        story.append(Spacer(1, 0.5 * cm))

        # Критерии
        story.extend(self._build_criteria(analysis, styles))
        story.append(Spacer(1, 0.5 * cm))

        # Сильные стороны и улучшения
        story.extend(self._build_strengths_improvements(analysis, styles))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(
        self,
        analysis: ResumeAnalysisResponse,
        styles: dict,
    ) -> list:
        """Строит заголовок документа."""
        story = []

        # Заголовок
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=6,
            alignment=0,
        )
        title = Paragraph('Resume Analysis Report', title_style)
        story.append(title)

        # Метаинформация
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
        )
        file_name = analysis.file_name or 'Unknown'
        meta_text = f'File: <b>{file_name}</b> | Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        story.append(Paragraph(meta_text, meta_style))

        return story

    def _build_overall_score(
        self,
        analysis: ResumeAnalysisResponse,
        styles: dict,
    ) -> list:
        """Строит секцию общей оценки."""
        story = []

        # Заголовок
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=8,
        )
        story.append(Paragraph('Overall Score', heading_style))

        # Контейнер с оценкой и прогресс-баром
        score = analysis.overall_score
        score_color = self._get_score_color(score)

        # Таблица с оценкой и баром
        score_text = f'<font size=48 color="{score_color.hexValue()}" face="Helvetica-Bold">{score}</font><br/><font size=10>out of 10</font>'

        # Прогресс-бар как Flowable
        progress_bar = ProgressBar(score, width=150, height=20, color=score_color)

        score_data = [
            [
                Paragraph(score_text, styles['Normal']),
                progress_bar,
            ]
        ]

        score_table = Table(
            score_data,
            colWidths=[3 * cm, 10 * cm],
            rowHeights=[1.5 * cm],
        )
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 20),
        ]))

        story.append(score_table)
        return story

    def _build_summary(
        self,
        analysis: ResumeAnalysisResponse,
        styles: dict,
    ) -> list:
        """Строит секцию резюме."""
        story = []

        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=8,
        )
        story.append(Paragraph('Summary', heading_style))

        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=4,
        )
        story.append(Paragraph(analysis.summary, summary_style))

        return story

    def _build_criteria(
        self,
        analysis: ResumeAnalysisResponse,
        styles: dict,
    ) -> list:
        """Строит секцию с критериями анализа."""
        story = []

        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=8,
        )
        story.append(Paragraph('Analysis by Criteria', heading_style))

        # Таблица критериев
        criteria_names = {
            'skills': 'Technical Skills',
            'experience': 'Professional Experience',
            'structure': 'Document Structure',
            'language': 'Language & Tone',
        }

        for criterion_key, criterion_data in analysis.criteria.items():
            story.extend(
                self._build_criterion_section(
                    criterion_key,
                    criteria_names.get(criterion_key, criterion_key.title()),
                    criterion_data,
                    styles,
                )
            )
            story.append(Spacer(1, 0.3 * cm))

        return story

    def _build_criterion_section(
        self,
        key: str,
        name: str,
        criterion: dict,
        styles: dict,
    ) -> list:
        """Строит секцию для одного критерия."""
        story = []

        # Заголовок с оценкой
        score = criterion.score
        score_color = self._get_score_color(score)

        criterion_heading_style = ParagraphStyle(
            'CriterionHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=self.COLOR_ACCENT,
            spaceAfter=4,
        )

        heading_text = f'{name} <font color="{score_color.hexValue()}"><b>[{score}/10]</b></font>'
        story.append(Paragraph(heading_text, criterion_heading_style))

        # Фидбек
        feedback_style = ParagraphStyle(
            'Feedback',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            leftIndent=0.3 * cm,
            textColor=colors.HexColor('#333333'),
        )
        story.append(Paragraph(f'<b>Feedback:</b> {criterion.feedback}', feedback_style))

        # Рекомендации
        if criterion.suggestions:
            story.append(Spacer(1, 0.2 * cm))
            suggestion_style = ParagraphStyle(
                'Suggestion',
                parent=styles['Normal'],
                fontSize=9,
                leading=11,
                leftIndent=0.5 * cm,
                textColor=colors.HexColor('#666666'),
            )
            story.append(Paragraph('<b>Suggestions:</b>', suggestion_style))

            for suggestion in criterion.suggestions:
                bullet_style = ParagraphStyle(
                    'BulletItem',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    leftIndent=0.8 * cm,
                    textColor=colors.HexColor('#666666'),
                )
                story.append(Paragraph(f'• {suggestion}', bullet_style))

        return story

    def _build_strengths_improvements(
        self,
        analysis: ResumeAnalysisResponse,
        styles: dict,
    ) -> list:
        """Строит секцию со сильными сторонами и улучшениями."""
        story = []

        # Сильные стороны
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=8,
        )
        story.append(Paragraph('Top Strengths', heading_style))

        strength_style = ParagraphStyle(
            'Strength',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            leftIndent=0.5 * cm,
            textColor=self.COLOR_SUCCESS,
        )
        for strength in analysis.top_strengths:
            story.append(Paragraph(f'✓ {strength}', strength_style))

        story.append(Spacer(1, 0.5 * cm))

        # Приоритетные улучшения
        story.append(Paragraph('Key Improvements', heading_style))

        improvement_style = ParagraphStyle(
            'Improvement',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            leftIndent=0.5 * cm,
            textColor=self.COLOR_WARNING,
        )
        for improvement in analysis.top_improvements:
            story.append(Paragraph(f'→ {improvement}', improvement_style))

        return story

    def _get_score_color(self, score: int) -> colors.Color:
        """Возвращает цвет в зависимости от оценки."""
        if score >= 8:
            return self.COLOR_SUCCESS
        elif score >= 6:
            return self.COLOR_ACCENT
        elif score >= 4:
            return self.COLOR_WARNING
        else:
            return self.COLOR_DANGER
