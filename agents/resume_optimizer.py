"""
agents/resume_optimizer.py

Resume Optimization Agent

Responsibilities:
- Improve the professional summary, experience, and project descriptions.
- Fix grammar and suggest stronger action verbs.
- Rewrite weak bullet points in a professional tone.
"""

import json

from prompts.optimizer_prompt import OPTIMIZER_SYSTEM_PROMPT
from tools.utils import call_llm, safe_json_parse


EMPTY_OPTIMIZER_SCHEMA = {
    "improved_summary": "",
    "improved_experience": [],
    "improved_projects": [],
    "grammar_fixes": [],
    "action_verb_suggestions": [],
    "bullet_point_rewrites": [],
}


def optimize_resume(resume_data: dict, job_description: str) -> dict:
    """
    Generate optimization suggestions for a parsed resume.

    Args:
        resume_data: Structured resume data.
        job_description: Target job description text (may be empty),
            used to tailor tone and emphasis where relevant.

    Returns:
        dict: Optimization suggestions matching EMPTY_OPTIMIZER_SCHEMA's keys.
    """
    if not resume_data:
        return dict(EMPTY_OPTIMIZER_SCHEMA)

    user_message = (
        f"STRUCTURED RESUME DATA:\n{json.dumps(resume_data, indent=2)}\n\n"
        f"TARGET JOB DESCRIPTION (optional context):\n{job_description or 'Not provided'}"
    )

    response_text = call_llm(OPTIMIZER_SYSTEM_PROMPT, user_message)
    parsed = safe_json_parse(response_text)

    if not parsed:
        return dict(EMPTY_OPTIMIZER_SCHEMA)

    for key, default_value in EMPTY_OPTIMIZER_SCHEMA.items():
        parsed.setdefault(key, default_value)

    return parsed
