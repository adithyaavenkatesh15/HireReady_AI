"""
agents/report_generator.py

Report Generator

Combines the output of every agent (Resume Parser, ATS, Job Match,
Skill Gap, Resume Optimizer, Interview Prep) into a single structured
final report, plus a short natural-language executive summary.
"""

import json

from prompts.report_prompt import REPORT_SUMMARY_PROMPT
from tools.utils import call_llm


def _generate_executive_summary(combined_data: dict) -> str:
    """
    Ask the LLM for a short executive summary paragraph. Falls back to a
    simple templated summary if the LLM call fails.
    """
    try:
        user_message = f"Combined analysis data:\n{json.dumps(combined_data, indent=2)}"
        return call_llm(REPORT_SUMMARY_PROMPT, user_message).strip()
    except Exception:
        ats_score = combined_data.get("ats_score", "N/A")
        job_match = combined_data.get("job_match_percent", "N/A")
        return (
            f"This resume scored {ats_score}/100 on ATS friendliness and "
            f"{job_match}% on job match for the target role. Review the "
            "detailed sections below for specific improvement suggestions."
        )


def generate_final_report(
    resume_data: dict,
    ats_result: dict,
    job_match_result: dict,
    skill_gap_result: dict,
    optimizer_result: dict,
    interview_result: dict,
) -> dict:
    """
    Merge every agent's output into one structured final report dict.

    Args:
        resume_data: Output of the Resume Parser Agent.
        ats_result: Output of the ATS Evaluation Agent.
        job_match_result: Output of the Job Matching Agent.
        skill_gap_result: Output of the Skill Gap Analysis Agent.
        optimizer_result: Output of the Resume Optimization Agent.
        interview_result: Output of the Interview Preparation Agent.

    Returns:
        dict: The complete final report, ready for display, translation,
        voice narration, and PDF export.
    """
    report = {
        "candidate_name": resume_data.get("name", "Candidate"),
        "resume_data": resume_data,
    }

    report.update(ats_result)
    report.update(job_match_result)
    report.update(skill_gap_result)
    report.update(optimizer_result)
    report.update(interview_result)

    report["executive_summary"] = _generate_executive_summary(report)

    return report
