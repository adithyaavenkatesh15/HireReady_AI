"""
agents/interview_agent.py

Interview Preparation Agent

Responsibilities:
- Generate HR, technical, project, and behavioral interview questions.
- Provide follow-up questions and expected answer guidance.
- Assign an overall difficulty level.
"""

import json

from prompts.interview_prompt import INTERVIEW_SYSTEM_PROMPT
from tools.utils import call_llm, safe_json_parse


EMPTY_INTERVIEW_SCHEMA = {
    "hr_questions": [],
    "technical_questions": [],
    "project_questions": [],
    "behavioral_questions": [],
    "follow_up_questions": [],
    "expected_answers": [],
    "difficulty_level": "Beginner",
}


def generate_interview_prep(resume_data: dict, job_description: str, target_role: str) -> dict:
    """
    Generate a full interview preparation set tailored to the candidate's
    resume and target role.

    Args:
        resume_data: Structured resume data.
        job_description: Target job description text (may be empty).
        target_role: Target job role title selected by the user.

    Returns:
        dict: Interview prep results matching EMPTY_INTERVIEW_SCHEMA's keys.
    """
    if not resume_data:
        return dict(EMPTY_INTERVIEW_SCHEMA)

    user_message = (
        f"Target job role: {target_role or 'Not specified'}\n\n"
        f"STRUCTURED RESUME DATA:\n{json.dumps(resume_data, indent=2)}\n\n"
        f"JOB DESCRIPTION:\n{job_description or 'Not provided'}"
    )

    response_text = call_llm(INTERVIEW_SYSTEM_PROMPT, user_message)
    parsed = safe_json_parse(response_text)

    if not parsed:
        return dict(EMPTY_INTERVIEW_SCHEMA)

    for key, default_value in EMPTY_INTERVIEW_SCHEMA.items():
        parsed.setdefault(key, default_value)

    if parsed.get("difficulty_level") not in ("Beginner", "Intermediate", "Advanced"):
        parsed["difficulty_level"] = "Beginner"

    return parsed
