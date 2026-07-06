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

_HEADING_STYLE = ParagraphStyle(
    "SectionHeading",
    parent=_styles["Heading2"],
    textColor=colors.HexColor("#1F2937"),
    spaceBefore=14,
    spaceAfter=6,
)

_BODY_STYLE = ParagraphStyle(
    "Body",
    parent=_styles["BodyText"],
    fontSize=10.5,
    leading=15,
)


def _bullet_list(items: list) -> ListFlowable:
    """Build a ReportLab bullet list from a list of strings."""
    list_items = [ListItem(Paragraph(str(item), _BODY_STYLE)) for item in items]
    return ListFlowable(list_items, bulletType="bullet", leftIndent=14)


def _score_table(rows: list) -> Table:
    """Build a simple two-column score summary table."""
    table = Table(rows, colWidths=[8 * cm, 8 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ]
        )
    )
    return table


def generate_report_pdf(report: dict, candidate_name: str = "Candidate") -> str:
    """
    Generate a complete PDF report from the combined agent output and
    save it into the reports directory.

    Args:
        report: The combined final report dictionary (see
            agents/report_generator.py for its structure).
        candidate_name: Candidate's name for the report header.

    Returns:
        str: Full path to the generated PDF file.
    """
    filename = f"HireReady_Report_{int(time.time())}.pdf"
    output_path = os.path.join(REPORTS_DIR, filename)

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
    story.append(Paragraph("HireReady AI — Resume Intelligence Report", _styles["Title"]))
    story.append(Paragraph(f"Candidate: {candidate_name}", _BODY_STYLE))
    story.append(Spacer(1, 12))

    # Executive Summary
    story.append(Paragraph("Executive Summary", _HEADING_STYLE))
    story.append(Paragraph(report.get("executive_summary", "N/A"), _BODY_STYLE))

    # Score Overview
    story.append(Paragraph("Score Overview", _HEADING_STYLE))
    story.append(
        _score_table(
            [
                ["Metric", "Value"],
                ["ATS Score", f"{report.get('ats_score', 'N/A')} / 100"],
                ["Job Match", f"{report.get('job_match_percent', 'N/A')} %"],
                ["Difficulty Level", report.get("difficulty_level", "N/A")],
            ]
        )
    )

    # ATS Feedback
    story.append(Paragraph("ATS Evaluation", _HEADING_STYLE))
    story.append(Paragraph(report.get("formatting_feedback", ""), _BODY_STYLE))
    if report.get("missing_sections"):
        story.append(Paragraph("Missing Sections:", _BODY_STYLE))
        story.append(_bullet_list(report["missing_sections"]))
    if report.get("suggestions"):
        story.append(Paragraph("Suggestions:", _BODY_STYLE))
        story.append(_bullet_list(report["suggestions"]))

    # Job Match
    story.append(Paragraph("Job Match Analysis", _HEADING_STYLE))
    if report.get("strengths"):
        story.append(Paragraph("Strengths:", _BODY_STYLE))
        story.append(_bullet_list(report["strengths"]))
    if report.get("weaknesses"):
        story.append(Paragraph("Weaknesses:", _BODY_STYLE))
        story.append(_bullet_list(report["weaknesses"]))
    if report.get("missing_keywords"):
        story.append(Paragraph("Missing Keywords:", _BODY_STYLE))
        story.append(_bullet_list(report["missing_keywords"]))

    # Skill Gap
    story.append(Paragraph("Skill Gap Analysis", _HEADING_STYLE))
    if report.get("missing_technical_skills"):
        story.append(Paragraph("Missing Technical Skills:", _BODY_STYLE))
        story.append(_bullet_list(report["missing_technical_skills"]))
    if report.get("recommended_certifications"):
        story.append(Paragraph("Recommended Certifications:", _BODY_STYLE))
        story.append(_bullet_list(report["recommended_certifications"]))
    if report.get("career_roadmap"):
        story.append(Paragraph("Career Roadmap:", _BODY_STYLE))
        story.append(_bullet_list(report["career_roadmap"]))

    # Resume Optimization
    story.append(Paragraph("Resume Optimization", _HEADING_STYLE))
    if report.get("improved_summary"):
        story.append(Paragraph("Improved Summary:", _BODY_STYLE))
        story.append(Paragraph(report["improved_summary"], _BODY_STYLE))
    if report.get("bullet_point_rewrites"):
        story.append(Paragraph("Bullet Point Rewrites:", _BODY_STYLE))
        story.append(_bullet_list(report["bullet_point_rewrites"]))

    # Interview Preparation
    story.append(Paragraph("Interview Preparation", _HEADING_STYLE))
    for label, key in [
        ("HR Questions", "hr_questions"),
        ("Technical Questions", "technical_questions"),
        ("Project Questions", "project_questions"),
        ("Behavioral Questions", "behavioral_questions"),
    ]:
        if report.get(key):
            story.append(Paragraph(f"{label}:", _BODY_STYLE))
            story.append(_bullet_list(report[key]))

    document.build(story)

    return output_path
