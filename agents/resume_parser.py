"""
agents/resume_parser.py

Resume Parser Agent

Responsibilities:
- Extract name, education, skills, projects, experience, certifications,
  and achievements from raw resume text.
- Return the information as structured JSON.
"""

from prompts.parser_prompt import PARSER_SYSTEM_PROMPT
from tools.utils import call_llm, safe_json_parse, truncate_text


EMPTY_RESUME_SCHEMA = {
    "name": "",
    "email": "",
    "phone": "",
    "education": [],
    "skills": [],
    "projects": [],
    "experience": [],
    "certifications": [],
    "achievements": [],
}


def parse_resume(raw_text: str) -> dict:
    """
    Parse raw resume text into structured JSON using the LLM.

    Args:
        raw_text: Full extracted resume text (from tools/pdf_parser.py).

    Returns:
        dict: Structured resume data matching EMPTY_RESUME_SCHEMA's keys.
    """
    if not raw_text or not raw_text.strip():
        return dict(EMPTY_RESUME_SCHEMA)

    user_message = (
        "Extract structured information from the following resume text.\n\n"
        f"RESUME TEXT:\n{truncate_text(raw_text)}"
    )

    response_text = call_llm(PARSER_SYSTEM_PROMPT, user_message)
    parsed = safe_json_parse(response_text)

    if not parsed:
        return dict(EMPTY_RESUME_SCHEMA)

    # Ensure every expected key exists, even if the LLM omitted one
    for key, default_value in EMPTY_RESUME_SCHEMA.items():
        parsed.setdefault(key, default_value)

    return parsed
