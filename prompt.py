"""
prompt.py

Top-level prompt module for HireReady AI.

Individual agent prompts live in prompts/*.py (never hardcoded inside
agent files). This module defines the orchestrator-level system prompt
used for general conversation/voice interaction, and re-exports the
per-agent prompts for convenient importing.
"""

from prompts.parser_prompt import PARSER_SYSTEM_PROMPT
from prompts.ats_prompt import ATS_SYSTEM_PROMPT
from prompts.job_prompt import JOB_MATCH_SYSTEM_PROMPT
from prompts.skill_prompt import SKILL_GAP_SYSTEM_PROMPT
from prompts.optimizer_prompt import OPTIMIZER_SYSTEM_PROMPT
from prompts.interview_prompt import INTERVIEW_SYSTEM_PROMPT
from prompts.report_prompt import REPORT_SUMMARY_PROMPT

SYSTEM_PROMPT = """
You are HireReady AI, a multi-agent Resume Intelligence assistant.

You help candidates understand and improve their resumes through:

- Resume parsing
- ATS evaluation
- Job matching
- Skill gap analysis
- Resume optimization
- Interview preparation

When a user speaks to you directly (via text or voice) outside of the
structured analysis pipeline, be friendly, concise, and professional.
Guide them toward uploading a resume and selecting a target job role
so the full multi-agent analysis can run.

Never fabricate resume details. Always base your responses on the
structured data produced by the analysis agents.
"""

__all__ = [
    "SYSTEM_PROMPT",
    "PARSER_SYSTEM_PROMPT",
    "ATS_SYSTEM_PROMPT",
    "JOB_MATCH_SYSTEM_PROMPT",
    "SKILL_GAP_SYSTEM_PROMPT",
    "OPTIMIZER_SYSTEM_PROMPT",
    "INTERVIEW_SYSTEM_PROMPT",
    "REPORT_SUMMARY_PROMPT",
]
