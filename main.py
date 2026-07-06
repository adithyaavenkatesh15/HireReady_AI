"""
main.py

Core orchestration layer for HireReady AI.

Implements the LangGraph workflow that chains all six agents together:

    Resume Upload
        -> Resume Parser Agent
        -> ATS Agent
        -> Job Match Agent
        -> Skill Gap Agent
        -> Resume Optimizer Agent
        -> Interview Agent
        -> Report Generator
        -> Return Final Report
"""

from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from agents.resume_parser import parse_resume
from agents.ats_agent import evaluate_ats
from agents.job_match_agent import match_job
from agents.skill_gap_agent import analyze_skill_gap
from agents.resume_optimizer import optimize_resume
from agents.interview_agent import generate_interview_prep
from agents.report_generator import generate_final_report

from memory import add_report, set_selected_job_role


class ResumeAnalysisState(TypedDict, total=False):
    """
    Shared state object passed between every node in the LangGraph
    workflow. Each agent reads what it needs and writes its own output
    back into the state.
    """
    raw_text: str
    job_description: str
    target_role: str

    resume_data: dict
    ats_result: dict
    job_match_result: dict
    skill_gap_result: dict
    optimizer_result: dict
    interview_result: dict
    final_report: dict

    error: Optional[str]


# ---------------------------------------------------------------------
# Node functions — each wraps one agent
# ---------------------------------------------------------------------

def node_resume_parser(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["resume_data"] = parse_resume(state["raw_text"])
    return state


def node_ats_agent(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["ats_result"] = evaluate_ats(state["resume_data"], state["raw_text"])
    return state


def node_job_match_agent(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["job_match_result"] = match_job(
        state["resume_data"], state["raw_text"], state.get("job_description", "")
    )
    return state


def node_skill_gap_agent(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["skill_gap_result"] = analyze_skill_gap(
        state["resume_data"], state.get("job_description", ""), state.get("target_role", "")
    )
    return state


def node_resume_optimizer(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["optimizer_result"] = optimize_resume(
        state["resume_data"], state.get("job_description", "")
    )
    return state


def node_interview_agent(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["interview_result"] = generate_interview_prep(
        state["resume_data"], state.get("job_description", ""), state.get("target_role", "")
    )
    return state


def node_report_generator(state: ResumeAnalysisState) -> ResumeAnalysisState:
    state["final_report"] = generate_final_report(
        resume_data=state["resume_data"],
        ats_result=state["ats_result"],
        job_match_result=state["job_match_result"],
        skill_gap_result=state["skill_gap_result"],
        optimizer_result=state["optimizer_result"],
        interview_result=state["interview_result"],
    )
    return state


# ---------------------------------------------------------------------
# Build the LangGraph workflow
# ---------------------------------------------------------------------

def build_workflow():
    """
    Construct and compile the LangGraph StateGraph representing the
    full HireReady AI multi-agent pipeline.
    """
    graph = StateGraph(ResumeAnalysisState)

    graph.add_node("resume_parser", node_resume_parser)
    graph.add_node("ats_agent", node_ats_agent)
    graph.add_node("job_match_agent", node_job_match_agent)
    graph.add_node("skill_gap_agent", node_skill_gap_agent)
    graph.add_node("resume_optimizer", node_resume_optimizer)
    graph.add_node("interview_agent", node_interview_agent)
    graph.add_node("report_generator", node_report_generator)

    graph.set_entry_point("resume_parser")

    graph.add_edge("resume_parser", "ats_agent")
    graph.add_edge("ats_agent", "job_match_agent")
    graph.add_edge("job_match_agent", "skill_gap_agent")
    graph.add_edge("skill_gap_agent", "resume_optimizer")
    graph.add_edge("resume_optimizer", "interview_agent")
    graph.add_edge("interview_agent", "report_generator")
    graph.add_edge("report_generator", END)

    return graph.compile()


_workflow = None


def get_workflow():
    """Lazily build and cache the compiled LangGraph workflow."""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


def run_resume_analysis(raw_text: str, job_description: str = "", target_role: str = "") -> dict:
    """
    Run the full multi-agent resume analysis pipeline end to end.

    Args:
        raw_text: Extracted resume text (see tools/pdf_parser.py).
        job_description: Target job description text (optional).
        target_role: Target job role title (optional).

    Returns:
        dict: The final combined report (see agents/report_generator.py).
    """
    if target_role:
        set_selected_job_role(target_role)

    workflow = get_workflow()

    initial_state: ResumeAnalysisState = {
        "raw_text": raw_text,
        "job_description": job_description,
        "target_role": target_role,
    }

    final_state = workflow.invoke(initial_state)
    final_report = final_state["final_report"]

    add_report(final_report)

    return final_report


if __name__ == "__main__":
    print("=" * 60)
    print("HireReady AI — Multi-Agent Resume Intelligence Platform")
    print("=" * 60)
    print("\nThis module powers the Streamlit app (app.py).")
    print("Run the following command to launch the full UI:\n")
    print("    streamlit run app.py\n")
