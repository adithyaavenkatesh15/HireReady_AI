"""
tools/report_pdf.py

Generates a downloadable PDF version of the final HireReady AI report
using ReportLab.
"""

import os
import time

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)

from config import REPORTS_DIR

_styles = getSampleStyleSheet()


def get_font_for_language(language: str):
    """
    Register and return appropriate fonts for the target language.
    Falls back gracefully if fonts are missing.
    """
    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"

    # Indic languages
    if language in ["Tamil", "Hindi", "Telugu", "Kannada", "Malayalam"]:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            # Nirmala UI is the default Indic font on Windows 8/10/11
            pdfmetrics.registerFont(TTFont('Nirmala', 'Nirmala.ttf'))
            pdfmetrics.registerFont(TTFont('Nirmala-Bold', 'Nirmalab.ttf'))
            font_regular = 'Nirmala'
            font_bold = 'Nirmala-Bold'
        except Exception:
            pass
    # CJK (Chinese, Japanese, Korean)
    elif language in ["Chinese (Simplified)", "Japanese", "Korean"]:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            if language == "Japanese":
                pdfmetrics.registerFont(TTFont('MSGothic', 'msgothic.ttc'))
                font_regular = 'MSGothic'
                font_bold = 'MSGothic'
            elif language == "Chinese (Simplified)":
                pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
                font_regular = 'SimSun'
                font_bold = 'SimSun'
            elif language == "Korean":
                pdfmetrics.registerFont(TTFont('Malgun', 'malgun.ttf'))
                font_regular = 'Malgun'
                font_bold = 'Malgun'
        except Exception:
            pass
    # Western European languages and fallback
    else:
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            # Arial is universally available on Windows
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
            font_regular = 'Arial'
            font_bold = 'Arial-Bold'
        except Exception:
            pass

    return font_regular, font_bold


def _bullet_list(items: list, body_style: ParagraphStyle) -> ListFlowable:
    """Build a ReportLab bullet list from a list of strings."""
    list_items = [ListItem(Paragraph(str(item), body_style)) for item in items]
    return ListFlowable(list_items, bulletType="bullet", leftIndent=14)


def _score_table(rows: list, font_regular: str = "Helvetica", font_bold: str = "Helvetica-Bold") -> Table:
    """Build a simple two-column score summary table."""
    table = Table(rows, colWidths=[8 * cm, 8 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_regular),
                ("FONTNAME", (0, 0), (-1, 0), font_bold),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ]
        )
    )
    return table


def generate_report_pdf(report: dict, candidate_name: str = "Candidate", language: str = "English") -> str:
    """
    Generate a complete PDF report from the combined agent output and
    save it into the reports directory.

    Args:
        report: The combined final report dictionary (see
            agents/report_generator.py for its structure).
        candidate_name: Candidate's name for the report header.
        language: The target language of the report.

    Returns:
        str: Full path to the generated PDF file.
    """
    filename = f"HireReady_Report_{int(time.time())}.pdf"
    output_path = os.path.join(REPORTS_DIR, filename)

    font_regular, font_bold = get_font_for_language(language)

    # Dynamic styles based on dynamic fonts
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=_styles["Title"],
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#111827"),
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=_styles["Heading2"],
        fontName=font_bold,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=14,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=_styles["BodyText"],
        fontName=font_regular,
        fontSize=10.5,
        leading=15,
    )

    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
    )

    story = []

    # Title
    story.append(Paragraph("HireReady AI — Resume Intelligence Report", title_style))
    story.append(Paragraph(f"Candidate: {candidate_name}", body_style))
    story.append(Spacer(1, 12))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(report.get("executive_summary", "N/A"), body_style))

    # Score Overview
    story.append(Paragraph("Score Overview", heading_style))
    story.append(
        _score_table(
            [
                ["Metric", "Value"],
                ["ATS Score", f"{report.get('ats_score', 'N/A')} / 100"],
                ["Job Match", f"{report.get('job_match_percent', 'N/A')} %"],
                ["Difficulty Level", report.get("difficulty_level", "N/A")],
            ],
            font_regular=font_regular,
            font_bold=font_bold,
        )
    )

    # ATS Feedback
    story.append(Paragraph("ATS Evaluation", heading_style))
    story.append(Paragraph(report.get("formatting_feedback", ""), body_style))
    if report.get("missing_sections"):
        story.append(Paragraph("Missing Sections:", body_style))
        story.append(_bullet_list(report["missing_sections"], body_style))
    if report.get("suggestions"):
        story.append(Paragraph("Suggestions:", body_style))
        story.append(_bullet_list(report["suggestions"], body_style))

    # Job Match
    story.append(Paragraph("Job Match Analysis", heading_style))
    if report.get("strengths"):
        story.append(Paragraph("Strengths:", body_style))
        story.append(_bullet_list(report["strengths"], body_style))
    if report.get("weaknesses"):
        story.append(Paragraph("Weaknesses:", body_style))
        story.append(_bullet_list(report["weaknesses"], body_style))
    if report.get("missing_keywords"):
        story.append(Paragraph("Missing Keywords:", body_style))
        story.append(_bullet_list(report["missing_keywords"], body_style))

    # Skill Gap
    story.append(Paragraph("Skill Gap Analysis", heading_style))
    if report.get("missing_technical_skills"):
        story.append(Paragraph("Missing Technical Skills:", body_style))
        story.append(_bullet_list(report["missing_technical_skills"], body_style))
    if report.get("recommended_certifications"):
        story.append(Paragraph("Recommended Certifications:", body_style))
        story.append(_bullet_list(report["recommended_certifications"], body_style))
    if report.get("career_roadmap"):
        story.append(Paragraph("Career Roadmap:", body_style))
        story.append(_bullet_list(report["career_roadmap"], body_style))

    # Resume Optimization
    story.append(Paragraph("Resume Optimization", heading_style))
    if report.get("improved_summary"):
        story.append(Paragraph("Improved Summary:", body_style))
        story.append(Paragraph(report["improved_summary"], body_style))
    if report.get("bullet_point_rewrites"):
        story.append(Paragraph("Bullet Point Rewrites:", body_style))
        formatted_rewrites = []
        for bullet in report["bullet_point_rewrites"]:
            bullet_data = None
            if isinstance(bullet, dict):
                bullet_data = bullet
            elif isinstance(bullet, str):
                try:
                    import ast
                    bullet_data = ast.literal_eval(bullet)
                except Exception:
                    pass
            
            if isinstance(bullet_data, dict):
                orig = bullet_data.get("original", "")
                imp = bullet_data.get("improved", "")
                if isinstance(imp, list):
                    imp_str = "; ".join(imp)
                else:
                    imp_str = str(imp)
                formatted_rewrites.append(f"Original: {orig}\nAI Suggestion: {imp_str}")
            else:
                formatted_rewrites.append(str(bullet))
        story.append(_bullet_list(formatted_rewrites, body_style))

    # Interview Preparation
    story.append(Paragraph("Interview Preparation", heading_style))
    for label, key in [
        ("HR Questions", "hr_questions"),
        ("Technical Questions", "technical_questions"),
        ("Project Questions", "project_questions"),
        ("Behavioral Questions", "behavioral_questions"),
    ]:
        if report.get(key):
            story.append(Paragraph(f"{label}:", body_style))
            story.append(_bullet_list(report[key], body_style))

    document.build(story)

    return output_path
