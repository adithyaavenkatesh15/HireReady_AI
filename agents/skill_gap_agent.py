"""
agents/skill_gap_agent.py

Skill Gap Analysis Agent

Responsibilities:
- Identify missing technical and soft skills relative to the target role.
- Suggest learning resources and certifications.
- Produce a career roadmap.
"""

import json

from prompts.skill_prompt import SKILL_GAP_SYSTEM_PROMPT
from tools.utils import call_llm, safe_json_parse


EMPTY_SKILL_GAP_SCHEMA = {
    "missing_technical_skills": [],
    "missing_soft_skills": [],
    "learning_resources": [],
    "recommended_certifications": [],
    "career_roadmap": [],
}


def analyze_skill_gap(resume_data: dict, job_description: str, target_role: str) -> dict:
    """
    Analyze the skill gap between a candidate's resume and their target role.

    Args:
        resume_data: Structured resume data.
        job_description: Target job description text (may be empty).
        target_role: Target job role title selected by the user.

    Returns:
        dict: Skill gap analysis matching EMPTY_SKILL_GAP_SCHEMA's keys.
    """
    if not resume_data:
        return dict(EMPTY_SKILL_GAP_SCHEMA)

    user_message = (
        f"Target job role: {target_role or 'Not specified'}\n\n"
        f"STRUCTURED RESUME DATA:\n{json.dumps(resume_data, indent=2)}\n\n"
        f"JOB DESCRIPTION:\n{job_description or 'Not provided'}"
    )

    response_text = call_llm(SKILL_GAP_SYSTEM_PROMPT, user_message)
    parsed = safe_json_parse(response_text)

    if not parsed:
        return dict(EMPTY_SKILL_GAP_SCHEMA)

    for key, default_value in EMPTY_SKILL_GAP_SCHEMA.items():
        parsed.setdefault(key, default_value)

    return parsed
