"""
tools/ats_score.py

Deterministic, rule-based ATS scoring helpers. These provide an
objective baseline that complements the LLM-driven qualitative feedback
produced by the ATS Evaluation Agent.
"""

REQUIRED_SECTIONS = [
    "experience",
    "education",
    "skills",
    "projects",
]


def calculate_section_score(resume_data: dict) -> int:
    """
    Score out of 40 based on presence of key resume sections.
    """
    score = 0
    points_per_section = 40 // len(REQUIRED_SECTIONS)

    for section in REQUIRED_SECTIONS:
        value = resume_data.get(section)
        if value:
            score += points_per_section

    return score


def calculate_length_score(raw_text: str) -> int:
    """
    Score out of 20 based on resume length. Very short resumes usually
    lack detail; extremely long resumes hurt ATS readability.
    """
    word_count = len(raw_text.split())

    if word_count < 150:
        return 5
    if word_count < 300:
        return 12
    if word_count <= 900:
        return 20
    if word_count <= 1300:
        return 14
    return 8


def calculate_contact_score(resume_data: dict) -> int:
    """
    Score out of 10 based on presence of contact details.
    """
    score = 0
    if resume_data.get("email"):
        score += 5
    if resume_data.get("phone"):
        score += 5
    return score


def find_missing_sections(resume_data: dict) -> list:
    """
    Return a list of required sections that are missing or empty.
    """
    missing = []
    for section in REQUIRED_SECTIONS:
        if not resume_data.get(section):
            missing.append(section)
    return missing


def calculate_baseline_ats_score(resume_data: dict, raw_text: str) -> int:
    """
    Combine rule-based sub-scores into a baseline ATS score out of 70.
    The remaining 30 points come from LLM-driven keyword density and
    formatting judgment, combined by the ATS agent.
    """
    section_score = calculate_section_score(resume_data)
    length_score = calculate_length_score(raw_text)
    contact_score = calculate_contact_score(resume_data)

    return section_score + length_score + contact_score
