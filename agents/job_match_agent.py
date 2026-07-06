"""
agents/job_match_agent.py

Job Matching Agent

Responsibilities:
- Compare resume against a target job description.
- Return job match percentage, missing keywords/technologies,
  strengths, and weaknesses.
"""

import json

from prompts.job_prompt import JOB_MATCH_SYSTEM_PROMPT
from tools.utils import call_llm, safe_json_parse, truncate_text
from tools.keyword_extractor import find_missing_keywords, calculate_keyword_overlap_percent
from tools.job_match import calculate_semantic_similarity


EMPTY_JOB_MATCH_SCHEMA = {
    "job_match_percent": 0,
    "missing_keywords": [],
    "missing_technologies": [],
    "strengths": [],
    "weaknesses": [],
}


def match_job(resume_data: dict, raw_text: str, job_description: str) -> dict:
    """
    Compare a parsed resume against a job description.

    Blends three signals into the final match percentage:
    1. LLM qualitative judgment
    2. Keyword overlap (tools/keyword_extractor.py)
    3. Semantic embedding similarity (tools/job_match.py, FAISS)

    Args:
        resume_data: Structured resume data.
        raw_text: Full extracted resume text.
        job_description: Target job description text.

    Returns:
        dict: Job match results matching EMPTY_JOB_MATCH_SCHEMA's keys.
    """
    if not job_description or not job_description.strip():
        return dict(EMPTY_JOB_MATCH_SCHEMA)

    keyword_overlap_score = calculate_keyword_overlap_percent(raw_text, job_description)

    try:
        semantic_score = calculate_semantic_similarity(raw_text, job_description)
    except Exception:
        # Embedding model unavailable/misconfigured: fall back gracefully
        semantic_score = keyword_overlap_score

    baseline_missing_keywords = find_missing_keywords(raw_text, job_description)

    user_message = (
        "Compare this resume against the job description below.\n\n"
        f"STRUCTURED RESUME DATA:\n{json.dumps(resume_data, indent=2)}\n\n"
        f"RESUME TEXT:\n{truncate_text(raw_text)}\n\n"
        f"JOB DESCRIPTION:\n{job_description}"
    )

    response_text = call_llm(JOB_MATCH_SYSTEM_PROMPT, user_message)
    parsed = safe_json_parse(response_text)

    if not parsed:
        result = dict(EMPTY_JOB_MATCH_SCHEMA)
        result["job_match_percent"] = round((keyword_overlap_score + semantic_score) / 2)
        result["missing_keywords"] = baseline_missing_keywords
        return result

    for key, default_value in EMPTY_JOB_MATCH_SCHEMA.items():
        parsed.setdefault(key, default_value)

    llm_score = parsed.get("job_match_percent", 0)
    try:
        llm_score = int(llm_score)
    except (TypeError, ValueError):
        llm_score = 0

    # Weighted blend: 50% LLM judgment, 25% keyword overlap, 25% semantic similarity
    parsed["job_match_percent"] = round(
        (llm_score * 0.5) + (keyword_overlap_score * 0.25) + (semantic_score * 0.25)
    )

    combined_missing = list(
        set(baseline_missing_keywords) | set(parsed.get("missing_keywords", []))
    )
    parsed["missing_keywords"] = combined_missing[:30]

    return parsed
