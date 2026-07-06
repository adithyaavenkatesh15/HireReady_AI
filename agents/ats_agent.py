"""
agents/ats_agent.py

ATS Evaluation Agent

Responsibilities:
- Calculate an ATS score covering formatting, readability, section
  order, and keyword density.
- Identify missing sections.
- Provide actionable suggestions.
"""

import json

from prompts.ats_prompt import ATS_SYSTEM_PROMPT
from tools.utils import call_llm, safe_json_parse, truncate_text
from tools.ats_score import calculate_baseline_ats_score, find_missing_sections


EMPTY_ATS_SCHEMA = {
    "ats_score": 0,
    "formatting_feedback": "",
    "readability_feedback": "",
    "section_order_feedback": "",
    "keyword_density_feedback": "",
    "missing_sections": [],
    "suggestions": [],
}


def evaluate_ats(resume_data: dict, raw_text: str) -> dict:
    """
    Evaluate a parsed resume for ATS friendliness.

    Combines a deterministic rule-based baseline score (tools/ats_score.py)
    with LLM-driven qualitative feedback for a more balanced final score.

    Args:
        resume_data: Structured resume data from the Resume Parser Agent.
        raw_text: Full extracted resume text.

    Returns:
        dict: ATS evaluation results matching EMPTY_ATS_SCHEMA's keys.
    """
    if not raw_text or not raw_text.strip():
        return dict(EMPTY_ATS_SCHEMA)

    baseline_score = calculate_baseline_ats_score(resume_data, raw_text)
    rule_based_missing = find_missing_sections(resume_data)

    user_message = (
        "Evaluate this resume for ATS friendliness.\n\n"
        f"STRUCTURED RESUME DATA:\n{json.dumps(resume_data, indent=2)}\n\n"
        f"RAW RESUME TEXT:\n{truncate_text(raw_text)}"
    )

    response_text = call_llm(ATS_SYSTEM_PROMPT, user_message)
    parsed = safe_json_parse(response_text)

    if not parsed:
        result = dict(EMPTY_ATS_SCHEMA)
        result["ats_score"] = baseline_score
        result["missing_sections"] = rule_based_missing
        return result

    for key, default_value in EMPTY_ATS_SCHEMA.items():
        parsed.setdefault(key, default_value)

    # Blend the rule-based score with the LLM's judgment for stability
    llm_score = parsed.get("ats_score", baseline_score)
    try:
        llm_score = int(llm_score)
    except (TypeError, ValueError):
        llm_score = baseline_score

    parsed["ats_score"] = round((baseline_score + llm_score) / 2)

    # Merge missing sections from both sources, removing duplicates
    combined_missing = list(set(rule_based_missing) | set(parsed.get("missing_sections", [])))
    parsed["missing_sections"] = combined_missing

    return parsed
