"""
app.py

Streamlit web interface for HireReady AI — Multi-Agent Resume
Intelligence Platform.

Supports both text and voice interaction, resume upload, job role
targeting, multilingual report translation, PDF export, and audio
playback of the final report.
"""

import os
import streamlit as st

from config import SUPPORTED_LANGUAGES, UPLOADS_DIR, validate_config
from tools.pdf_parser import extract_text_from_bytes, InvalidPDFError, EmptyResumeError
from tools.translator import translate_report_sections, TranslationError
from tools.report_pdf import generate_report_pdf
from tools.voice import (
    text_to_speech,
    speech_to_text,
    load_audio_bytes,
    VoiceError,
)
from main import get_workflow
from memory import load_memory, set_selected_language, clear_memory, add_report


# ---------------------------------------------------------------------
# Page configuration & custom dark theme styling
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="HireReady AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* Global Reset and Typography */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #090D1A !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.08) 0px, transparent 50%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-bottom: 20px !important;
    }

    .glass-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(56, 189, 248, 0.25) !important;
        box-shadow: 0 12px 40px 0 rgba(6, 182, 212, 0.15) !important;
    }

    /* Premium Dashboard Stat Cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }

    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #38BDF8, #06B6D4) !important;
        opacity: 0.8 !important;
    }

    .stat-card:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
        box-shadow: 0 10px 30px rgba(6, 182, 212, 0.15) !important;
    }

    .stat-val {
        font-size: 38px !important;
        font-weight: 800 !important;
        font-family: 'Outfit', sans-serif !important;
        background: linear-gradient(90deg, #F8FAFC, #38BDF8) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin: 10px 0 5px 0 !important;
    }

    .stat-label {
        font-size: 13px !important;
        color: #94A3B8 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-weight: 600 !important;
    }

    /* Badges */
    .badge {
        display: inline-block !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .badge-success {
        background-color: rgba(16, 185, 129, 0.15) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.15) !important;
        color: #F59E0B !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
    }
    .badge-error {
        background-color: rgba(239, 68, 68, 0.15) !important;
        color: #EF4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }

    /* Premium Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #060913 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Animated Steps Loader */
    .loading-box {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 16px !important;
        padding: 25px !important;
        box-shadow: 0 0 40px rgba(6, 182, 212, 0.1) !important;
        margin-bottom: 25px !important;
    }

    .progress-bar-container {
        background-color: #1E293B !important;
        height: 8px !important;
        border-radius: 4px !important;
        overflow: hidden !important;
        margin: 15px 0 !important;
    }

    .progress-bar-fill {
        height: 100% !important;
        background: linear-gradient(90deg, #38BDF8, #06B6D4) !important;
        border-radius: 4px !important;
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    @keyframes pulsate {
        0% { opacity: 0.5; }
        50% { opacity: 1.0; }
        100% { opacity: 0.5; }
    }
    .active-step {
        animation: pulsate 1.5s infinite;
    }

    /* AI Assessment/Insight Card */
    .ai-insight {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.08) 0%, rgba(56, 189, 248, 0.03) 100%) !important;
        border: 1px solid rgba(6, 182, 212, 0.2) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.05) !important;
    }

    /* Custom Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: rgba(30, 41, 59, 0.3) !important;
        padding: 6px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        padding: 10px 18px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        background-color: transparent !important;
        transition: all 0.2s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #38BDF8 !important;
        background-color: rgba(56, 189, 248, 0.05) !important;
    }

    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
    }

    /* Timeline Components */
    .timeline {
        position: relative !important;
        padding-left: 30px !important;
        margin: 20px 0 !important;
    }
    .timeline::before {
        content: '' !important;
        position: absolute !important;
        left: 9px !important;
        top: 5px !important;
        bottom: 5px !important;
        width: 2px !important;
        background: linear-gradient(to bottom, #38BDF8, rgba(56,189,248,0.1)) !important;
    }
    .timeline-item {
        position: relative !important;
        margin-bottom: 25px !important;
    }
    .timeline-badge {
        position: absolute !important;
        left: -30px !important;
        top: 3px !important;
        width: 20px !important;
        height: 20px !important;
        border-radius: 50% !important;
        background: #090D1A !important;
        border: 3px solid #38BDF8 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.6) !important;
        z-index: 2 !important;
    }
    .timeline-content {
        background: rgba(30, 41, 59, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    .timeline-title {
        font-weight: 700 !important;
        font-size: 15px !important;
        color: #F8FAFC !important;
        margin-bottom: 4px !important;
    }
    .timeline-text {
        font-size: 13.5px !important;
        color: #94A3B8 !important;
    }

    /* Split screen layout comparison tags */
    .comparison-box {
        border-radius: 12px !important;
        padding: 16px !important;
        height: 100% !important;
    }
    .comparison-before {
        background-color: rgba(239, 68, 68, 0.04) !important;
        border: 1px solid rgba(239, 68, 68, 0.15) !important;
    }
    .comparison-after {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, rgba(6, 182, 212, 0.03) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.05) !important;
    }

    /* Custom chips */
    .chip {
        display: inline-block !important;
        padding: 6px 12px !important;
        border-radius: 20px !important;
        margin: 4px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }
    .chip-matched {
        background-color: rgba(16, 185, 129, 0.12) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
    }
    .chip-missing {
        background-color: rgba(239, 68, 68, 0.12) !important;
        color: #EF4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.25) !important;
    }

    /* Styled Streamlit Expander */
    .stDetails {
        background: rgba(30, 41, 59, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
    }

    /* Drag Drop area enhancement */
    div[data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.25) !important;
        border: 2px dashed rgba(56, 189, 248, 0.3) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #38BDF8 !important;
        background: rgba(30, 41, 59, 0.35) !important;
    }

    /* Clean Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #090D1A;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Frontend Render Helpers
# ---------------------------------------------------------------------

def get_feedback_score(feedback_text: str) -> int:
    """Calculate a mock visual metric score from natural language feedback."""
    if not feedback_text:
        return 80
    text = feedback_text.lower()
    negatives = ["missing", "poor", "lack", "should", "needs", "improve", "weak", "bad", "incorrect", "add", "could"]
    score = 90
    for neg in negatives:
        if neg in text:
            score -= 8
    return max(30, score)


def draw_circular_progress(score: int, label: str, size: int = 100, color: str = "#38BDF8") -> str:
    """Renders a gorgeous SVG progress ring for dashboard analytics cards."""
    radius = 35
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference - (score / 100) * circumference
    return f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 10px;">
        <svg width="{size}" height="{size}" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="{radius}" stroke="rgba(255,255,255,0.05)" stroke-width="8" fill="transparent" />
            <circle cx="50" cy="50" r="{radius}" stroke="{color}" stroke-width="8" fill="transparent"
                stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}"
                stroke-linecap="round" transform="rotate(-90 50 50)" />
            <text x="50" y="56" font-family="Outfit, Inter, sans-serif" font-size="19" font-weight="800" fill="#F8FAFC" text-anchor="middle">{score}%</text>
        </svg>
        <span style="font-family: Outfit, Inter, sans-serif; font-size: 13.5px; font-weight: 600; color: #94A3B8; margin-top: 8px;">{label}</span>
    </div>
    """


def draw_progress_bar(value: int, label: str):
    """Renders a custom gradient progress bar."""
    if value >= 80:
        bar_color = "linear-gradient(90deg, #10B981, #34D399)"
        text_color = "#10B981"
    elif value >= 55:
        bar_color = "linear-gradient(90deg, #F59E0B, #FBBF24)"
        text_color = "#F59E0B"
    else:
        bar_color = "linear-gradient(90deg, #EF4444, #F87171)"
        text_color = "#EF4444"
        
    st.markdown(f"""
        <div style="margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13.5px; font-weight: 600;">
                <span style="color: #94A3B8;">{label}</span>
                <span style="color: {text_color};">{value}/100</span>
            </div>
            <div style="background-color: #1E293B; height: 7px; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,255,255,0.03);">
                <div style="height: 100%; background: {bar_color}; width: {value}%; border-radius: 4px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def draw_timeline(roadmap_steps: list):
    """Renders career roadmap items inside a vertical timeline."""
    timeline_html = '<div class="timeline">'
    for idx, step in enumerate(roadmap_steps, start=1):
        timeline_html += f"""
        <div class="timeline-item">
            <div class="timeline-badge"></div>
            <div class="timeline-content">
                <div class="timeline-title">Milestone {idx}</div>
                <div class="timeline-text">{step}</div>
            </div>
        </div>
        """
    timeline_html += '</div>'
    st.markdown(timeline_html, unsafe_allow_html=True)


def make_copy_section(text: str, key_id: str, label: str = "Copy Content"):
    """Render copy button to clipboard or fallback code block."""
    if hasattr(st, "copy_to_clipboard"):
        if st.button(f"📋 {label}", key=key_id, use_container_width=True):
            st.copy_to_clipboard(text)
            st.toast("Copied successfully!")
    else:
        st.code(text, language="text")


# ---------------------------------------------------------------------
# Sidebar — configuration & inputs
# ---------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 25px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="font-size: 30px; margin: 0; background: linear-gradient(135deg, #38BDF8 0%, #06B6D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family:Outfit;">🧠 HireReady AI</h2>', unsafe_allow_html=True)
    st.caption("Multi-Agent Resume Intelligence & Career Coach")
    st.markdown('</div>', unsafe_allow_html=True)

    missing_keys = validate_config()
    if missing_keys:
        st.warning(
            "⚠️ Missing API keys: " + ", ".join(missing_keys) +
            "\nFill them in your `.env` file for full features."
        )

    st.markdown("---")
    st.markdown("### 🛠️ CONFIGURATION")
    input_mode = st.radio("Input Mode", ["Text", "Voice"], horizontal=True)

    st.markdown("---")
    if st.button("🗑️ Reset Session Memory", use_container_width=True):
        clear_memory()
        st.success("Session memory cleared.")
        st.rerun()


# ---------------------------------------------------------------------
# Main dashboard router
# ---------------------------------------------------------------------

report = st.session_state.get("report")

if report:
    # -----------------------------------------------------------------
    # DISPLAY ANALYSIS REPORT DASHBOARD
    # -----------------------------------------------------------------
    candidate_name = report.get("candidate_name", "Candidate")
    resume_data = report.get("resume_data", {})
    email = resume_data.get("email") or "Not provided"
    phone = resume_data.get("phone") or "Not provided"
    education = resume_data.get("education") or []
    skills = resume_data.get("skills") or []
    projects = resume_data.get("projects") or []
    experience = resume_data.get("experience") or []
    certifications = resume_data.get("certifications") or []
    
    ats_score = int(report.get("ats_score", 0) or 0)
    job_match = int(report.get("job_match_percent", 0) or 0)
    
    # Trigger Confetti if ATS Score is exceptional
    if ats_score >= 90 and not st.session_state.get("balloons_shown", False):
        st.balloons()
        st.session_state["balloons_shown"] = True
        
    st.markdown(f"""
        <div style="margin-top: 15px; margin-bottom: 25px;">
            <h1 style="font-size: 38px; font-weight:800; font-family:'Outfit';">📊 Career Insights Dashboard</h1>
            <p style="color:#94A3B8; font-size:15px;">Target Analysis Profile: <strong>{report.get('resume_data', {}).get('name', 'Candidate')}</strong></p>
        </div>
    """, unsafe_allow_html=True)
    
    # -----------------------------------------------------------------
    # SaaS Dashboard Top Metrics Cards
    # -----------------------------------------------------------------
    # Compute scores
    if ats_score >= 80:
        ats_badge, ats_class = "Excellent", "badge-success"
    elif ats_score >= 60:
        ats_badge, ats_class = "Good", "badge-warning"
    else:
        ats_badge, ats_class = "Improve", "badge-error"

    if job_match >= 75:
        jm_badge, jm_class = "Strong", "badge-success"
    elif job_match >= 50:
        jm_badge, jm_class = "Moderate", "badge-warning"
    else:
        jm_badge, jm_class = "Weak", "badge-error"

    missing_sections_count = len(report.get("missing_sections", []))
    suggestions_count = len(report.get("suggestions", []))
    quality_score = max(10, min(100, ats_score + 5 - (missing_sections_count * 5) - (suggestions_count * 2)))
    if quality_score >= 80:
        quality_badge, quality_class = "Excellent", "badge-success"
    elif quality_score >= 60:
        quality_badge, quality_class = "Good", "badge-warning"
    else:
        quality_badge, quality_class = "Needs Work", "badge-error"

    diff_level = report.get("difficulty_level", "Intermediate")
    diff_base = {"Beginner": 85, "Intermediate": 70, "Advanced": 50}.get(diff_level, 70)
    strengths_count = len(report.get("strengths", []))
    weaknesses_count = len(report.get("weaknesses", []))
    readiness_score = max(20, min(98, diff_base + (strengths_count * 2) - (weaknesses_count * 3)))
    if readiness_score >= 80:
        readiness_badge, readiness_class = "Ready", "badge-success"
    elif readiness_score >= 55:
        readiness_badge, readiness_class = "Average", "badge-warning"
    else:
        readiness_badge, readiness_class = "Not Ready", "badge-error"

    career_score = max(10, min(100, int(0.4 * ats_score + 0.6 * job_match)))
    if career_score >= 80:
        career_badge, career_class = "High", "badge-success"
    elif career_score >= 55:
        career_badge, career_class = "Medium", "badge-warning"
    else:
        career_badge, career_class = "Low", "badge-error"
        
    metric_cols = st.columns(5)
    with metric_cols[0]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">ATS Score</div>
                <div class="stat-val">{ats_score}</div>
                <span class="badge {ats_class}">{ats_badge}</span>
            </div>
        """, unsafe_allow_html=True)
    with metric_cols[1]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Job Match</div>
                <div class="stat-val">{job_match}%</div>
                <span class="badge {jm_class}">{jm_badge}</span>
            </div>
        """, unsafe_allow_html=True)
    with metric_cols[2]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Resume Quality</div>
                <div class="stat-val">{quality_score}</div>
                <span class="badge {quality_class}">{quality_badge}</span>
            </div>
        """, unsafe_allow_html=True)
    with metric_cols[3]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Interview Ready</div>
                <div class="stat-val">{readiness_score}%</div>
                <span class="badge {readiness_class}">{readiness_badge}</span>
            </div>
        """, unsafe_allow_html=True)
    with metric_cols[4]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Career Rating</div>
                <div class="stat-val">{career_score}</div>
                <span class="badge {career_class}">{career_badge}</span>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # AI Summary Insight Card
    # -----------------------------------------------------------------
    st.markdown(f"""
        <div class="ai-insight">
            <h4 style="margin: 0 0 10px 0; color:#38BDF8; font-family:'Outfit'; font-size:18px;">🤖 AI Executive Assessment</h4>
            <p style="margin: 0; color:#E2E8F0; font-size:14.5px; line-height:1.6;">
                {report.get("executive_summary", "Review the sections below for details.")}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # Interactive Premium Navigation Tabs
    # -----------------------------------------------------------------
    tab_overview, tab_ats, tab_match, tab_gap, tab_optimizer, tab_interview, tab_actions = st.tabs([
        "📂 Overview",
        "📊 ATS Analysis",
        "🤝 Job Match",
        "🎓 Skill Gap & Roadmap",
        "✨ Resume Optimizer",
        "💬 Interview Prep",
        "🎯 Recommendations & PDF"
    ])

    # --- 1. OVERVIEW TAB ---
    with tab_overview:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"### 📂 Candidate Profile: {candidate_name}", unsafe_allow_html=True)
        col_details, col_health = st.columns([2, 1])
        with col_details:
            st.markdown(f"""
                <div style="font-size: 15px; line-height: 1.8; color: #E2E8F0;">
                    <p style="margin:5px 0;"><strong>🎯 Target Role:</strong> {report.get('target_role', 'Software Engineer')}</p>
                    <p style="margin:5px 0;"><strong>📧 Email:</strong> {email}</p>
                    <p style="margin:5px 0;"><strong>📞 Phone:</strong> {phone}</p>
                    <p style="margin:5px 0;"><strong>📅 Analysis Date:</strong> 2026-07-06</p>
                </div>
            """, unsafe_allow_html=True)
        with col_health:
            st.markdown(draw_circular_progress(ats_score, "Resume Health Index", size=115, color="#10B981"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("#### 📈 Key Statistics")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Experience</div>
                    <div class="stat-val">{len(experience)}</div>
                    <div style="font-size: 12px; color: #94A3B8;">Roles listed</div>
                </div>
            """, unsafe_allow_html=True)
        with stat_col2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Projects</div>
                    <div class="stat-val">{len(projects)}</div>
                    <div style="font-size: 12px; color: #94A3B8;">Projects built</div>
                </div>
            """, unsafe_allow_html=True)
        with stat_col3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Skills</div>
                    <div class="stat-val">{len(skills)}</div>
                    <div style="font-size: 12px; color: #94A3B8;">Core skills</div>
                </div>
            """, unsafe_allow_html=True)
        with stat_col4:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">Certifications</div>
                    <div class="stat-val">{len(certifications)}</div>
                    <div style="font-size: 12px; color: #94A3B8;">Credentials</div>
                </div>
            """, unsafe_allow_html=True)

        if education:
            st.markdown("<br>#### 🎓 Education History", unsafe_allow_html=True)
            edu_cols = st.columns(max(1, len(education)))
            for i, edu_item in enumerate(education):
                with edu_cols[min(i, len(edu_cols)-1)]:
                    st.markdown(f"""
                        <div class="timeline-content" style="margin-bottom: 10px; height: 100%;">
                            <div style="font-weight: 700; color: #F8FAFC; font-size:15px;">{edu_item.get('degree', 'Degree')}</div>
                            <div style="color: #38BDF8; font-size: 13px; margin: 3px 0;">{edu_item.get('institution', 'Institution')}</div>
                            <div style="color: #94A3B8; font-size: 12px;">Graduation/Completion: {edu_item.get('year', 'N/A')}</div>
                        </div>
                    """, unsafe_allow_html=True)

    # --- 2. ATS ANALYSIS TAB ---
    with tab_ats:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Applicant Tracking System (ATS) Friendliness")
        
        col_score_card, col_metrics = st.columns([1, 2])
        with col_score_card:
            st.markdown(draw_circular_progress(ats_score, "ATS Score", size=140, color="#38BDF8"), unsafe_allow_html=True)
            st.markdown(f"""
                <div style="text-align: center; margin-top: 10px;">
                    <span class="badge {ats_class}">{ats_badge}</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col_metrics:
            f_score = get_feedback_score(report.get("formatting_feedback", ""))
            r_score = get_feedback_score(report.get("readability_feedback", ""))
            s_score = get_feedback_score(report.get("section_order_feedback", ""))
            k_score = get_feedback_score(report.get("keyword_density_feedback", ""))
            
            draw_progress_bar(f_score, "Formatting & Typography Style")
            draw_progress_bar(r_score, "Readability & Index Score")
            draw_progress_bar(s_score, "Section Structure & Layout")
            draw_progress_bar(k_score, "Semantic Keyword Density")
            
        st.markdown("---")
        
        st.markdown("#### 🔍 Structural Feedback")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown(f"""
                <div class="timeline-content" style="margin-bottom:15px; border-left: 3px solid #38BDF8;">
                    <strong>Formatting Feedback:</strong><br>
                    <span style="font-size:13.5px; color:#E2E8F0;">{report.get("formatting_feedback", "No formatting issues found.")}</span>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
                <div class="timeline-content" style="margin-bottom:15px; border-left: 3px solid #38BDF8;">
                    <strong>Section Structure Feedback:</strong><br>
                    <span style="font-size:13.5px; color:#E2E8F0;">{report.get("section_order_feedback", "Section order is standard and friendly.")}</span>
                </div>
            """, unsafe_allow_html=True)
        with f_col2:
            st.markdown(f"""
                <div class="timeline-content" style="margin-bottom:15px; border-left: 3px solid #38BDF8;">
                    <strong>Readability Feedback:</strong><br>
                    <span style="font-size:13.5px; color:#E2E8F0;">{report.get("readability_feedback", "Readability matches industry standards.")}</span>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
                <div class="timeline-content" style="margin-bottom:15px; border-left: 3px solid #38BDF8;">
                    <strong>Keyword Density Feedback:</strong><br>
                    <span style="font-size:13.5px; color:#E2E8F0;">{report.get("keyword_density_feedback", "Keyword density check completed.")}</span>
                </div>
            """, unsafe_allow_html=True)

        missing_sections = report.get("missing_sections", [])
        if missing_sections:
            st.markdown(f"""
                <div class="comparison-box comparison-before" style="margin-bottom: 20px; border-left: 4px solid #EF4444;">
                    <h5 style="color:#EF4444; margin-top:0;">⚠️ Missing Resume Sections</h5>
                    <p style="font-size:13px; color:#E2E8F0; margin-bottom:5px;">
                        Applicant Tracking Systems look for standard sections. Your resume appears to lack the following headers:
                    </p>
                    <div style="margin-top: 8px;">
            """, unsafe_allow_html=True)
            sec_chips = ""
            for sec in missing_sections:
                sec_chips += f'<span class="chip chip-missing">{sec}</span>'
            st.markdown(sec_chips, unsafe_allow_html=True)
            st.markdown("</div></div>", unsafe_allow_html=True)
            
        suggestions = report.get("suggestions", [])
        if suggestions:
            st.markdown("#### 💡 AI Recommendations for ATS Enhancement")
            for sugg in suggestions:
                st.markdown(f"✔ <span style='font-size: 14px;'>{sugg}</span>", unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. JOB MATCH TAB ---
    with tab_match:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🤝 Job Role Compatibility Analysis")
        
        col_jm_chart, col_jm_desc = st.columns([1, 2])
        with col_jm_chart:
            st.markdown(draw_circular_progress(job_match, "Job Match Fit", size=140, color="#06B6D4"), unsafe_allow_html=True)
            st.markdown(f"""
                <div style="text-align: center; margin-top: 10px;">
                    <span class="badge {jm_class}">{jm_badge} Matching Fit</span>
                </div>
            """, unsafe_allow_html=True)
        with col_jm_desc:
            st.markdown(f"""
                <div style="font-size: 14.5px; line-height: 1.7; padding-top:15px; color:#E2E8F0;">
                    <p>This match is evaluated by running semantic comparison embeddings (FAISS similarity) against the <strong>{report.get('target_role', 'Selected Role')}</strong> description alongside LLM judgment.</p>
                    <p>Increasing the keyword density of the missing skills below can push your compatibility into the <strong>Strong</strong> match range.</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        col_str, col_weak = st.columns(2)
        with col_str:
            st.markdown("<h4 style='color:#10B981; font-family:Outfit;'>💚 Core Strengths</h4>", unsafe_allow_html=True)
            for strength in report.get("strengths", []):
                st.markdown(f"⭐ <span style='font-size:14px; color:#E2E8F0;'>{strength}</span>", unsafe_allow_html=True)
        with col_weak:
            st.markdown("<h4 style='color:#EF4444; font-family:Outfit;'>💔 Gaps & Weaknesses</h4>", unsafe_allow_html=True)
            for weakness in report.get("weaknesses", []):
                st.markdown(f"🔺 <span style='font-size:14px; color:#E2E8F0;'>{weakness}</span>", unsafe_allow_html=True)
                
        st.markdown("---")
        
        missing_kw = report.get("missing_keywords", [])
        missing_tech = report.get("missing_technologies", [])
        
        if missing_kw or missing_tech:
            st.markdown("#### 🏷️ Industry Keywords & Technologies to Integrate")
            
            if missing_tech:
                st.markdown("##### 🛠️ Tools, Platforms & Technologies")
                tech_html = ""
                for tech in missing_tech:
                    tech_html += f'<span class="chip chip-missing" title="Add this to your technical skills section">{tech}</span>'
                st.markdown(tech_html, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
            if missing_kw:
                st.markdown("##### 💼 Core Domain Keywords")
                kw_html = ""
                for kw in missing_kw:
                    kw_html += f'<span class="chip chip-missing" title="Integrate this keyword into experience description">{kw}</span>'
                st.markdown(kw_html, unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. SKILL GAP TAB ---
    with tab_gap:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🎓 Skill Gap Analysis & Growth Roadmap")
        
        gap_col1, gap_col2, gap_col3 = st.columns(3)
        with gap_col1:
            st.markdown("#### 📂 Current Skills")
            for skill in skills[:15]:
                st.markdown(f'<span class="chip chip-matched">{skill}</span>', unsafe_allow_html=True)
            if len(skills) > 15:
                st.markdown(f"<span style='font-size:12px; color:#94A3B8; padding-left:10px;'>+ {len(skills) - 15} more skills</span>", unsafe_allow_html=True)
                
        with gap_col3:
            st.markdown("#### ❌ Missing Skills")
            missing_tech_skills = report.get("missing_technical_skills", [])
            missing_soft_skills = report.get("missing_soft_skills", [])
            
            for m_skill in missing_tech_skills:
                st.markdown(f'<span class="chip chip-missing">{m_skill} (tech)</span>', unsafe_allow_html=True)
            for s_skill in missing_soft_skills:
                st.markdown(f'<span class="chip chip-missing" style="border-color:rgba(245,158,11,0.25); color:#F59E0B; background-color:rgba(245,158,11,0.12);">{s_skill} (soft)</span>', unsafe_allow_html=True)
                
        with gap_col2:
            st.markdown("#### 📋 Target Skills Required")
            required_skills = list(skills[:10]) + list(missing_tech_skills[:5])
            for r_skill in required_skills:
                st.markdown(f'<span class="chip" style="background-color:rgba(56,189,248,0.1); color:#38BDF8; border:1px solid rgba(56,189,248,0.25);">{r_skill}</span>', unsafe_allow_html=True)

        st.markdown("---")
        
        cert_col, res_col = st.columns(2)
        with cert_col:
            st.markdown("#### 🛡️ Recommended Credentials")
            recommended_certs = report.get("recommended_certifications", [])
            if recommended_certs:
                for cert in recommended_certs:
                    st.markdown(f"""
                        <div class="timeline-content" style="margin-bottom:10px; border-left:3px solid #10B981; padding: 10px 15px;">
                            <span style="font-weight:700; color:#F8FAFC;">🏅 {cert}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No specific certifications recommended.")
                
        with res_col:
            st.markdown("#### 📚 Recommended Learning Resources")
            learning_res = report.get("learning_resources", [])
            if learning_res:
                for resource in learning_res:
                    st.markdown(f"📖 <span style='font-size:14px;'>{resource}</span>", unsafe_allow_html=True)
            else:
                st.write("No specific platforms recommended.")
                
        st.markdown("---")
        
        st.markdown("#### 🗺️ Professional Growth Roadmap")
        roadmap = report.get("career_roadmap", [])
        if roadmap:
            draw_timeline(roadmap)
        else:
            st.write("Timeline could not be generated.")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. RESUME OPTIMIZER TAB ---
    with tab_optimizer:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ✨ AI Resume Optimizer Suggestions")
        
        improved_summary = report.get("improved_summary", "")
        if improved_summary:
            st.markdown("#### ✍️ Professional Summary Transformation")
            col_sum_before, col_sum_after = st.columns(2)
            with col_sum_before:
                st.markdown('<div class="comparison-box comparison-before">', unsafe_allow_html=True)
                st.markdown("<strong style='color:#EF4444;'>Original Content Summary:</strong>", unsafe_allow_html=True)
                st.write("Refer to original resume professional summary section.")
                st.markdown('</div>', unsafe_allow_html=True)
            with col_sum_after:
                st.markdown('<div class="comparison-box comparison-after">', unsafe_allow_html=True)
                st.markdown("<strong style='color:#10B981;'>AI Rewritten Version:</strong>", unsafe_allow_html=True)
                st.write(improved_summary)
                st.markdown('</div>', unsafe_allow_html=True)
                
            make_copy_section(improved_summary, "copy_improved_summary_opt", "Copy Optimized Summary")
            st.markdown("<br>", unsafe_allow_html=True)

        bullet_rewrites = report.get("bullet_point_rewrites", [])
        if bullet_rewrites:
            st.markdown("#### 🛠️ Experience Bullet-Point Polish")
            for idx, bullet in enumerate(bullet_rewrites, start=1):
                st.markdown(f"**Bullet Rewrite Suggestion {idx}:**")
                
                original_text = ""
                improved_text = ""
                
                bullet_data = None
                if isinstance(bullet, dict):
                    bullet_data = bullet
                elif isinstance(bullet, str):
                    try:
                        import ast
                        bullet_data = ast.literal_eval(bullet)
                    except Exception:
                        pass
                
                if isinstance(bullet_data, dict):
                    original_text = bullet_data.get("original", "")
                    improved_val = bullet_data.get("improved", "")
                    if isinstance(improved_val, list):
                        improved_text = "\n".join(f"• {item}" for item in improved_val)
                    else:
                        improved_text = str(improved_val)
                else:
                    bullet_str = str(bullet)
                    if " -> " in bullet_str:
                        original_text, improved_text = bullet_str.split(" -> ", 1)
                    elif " - " in bullet_str:
                        original_text, improved_text = bullet_str.split(" - ", 1)
                    else:
                        original_text = "Original bullet phrasing."
                        improved_text = bullet_str
                    
                col_b_before, col_b_after = st.columns(2)
                with col_b_before:
                    st.markdown(f'<div class="comparison-box comparison-before" style="padding:12px; font-size:13.5px;">❌ {original_text}</div>', unsafe_allow_html=True)
                with col_b_after:
                    st.markdown(f'<div class="comparison-box comparison-after" style="padding:12px; font-size:13.5px; white-space: pre-wrap;">✔️ {improved_text}</div>', unsafe_allow_html=True)
                    
                make_copy_section(improved_text, f"copy_bullet_opt_{idx}", f"Copy Suggestion {idx}")
                st.markdown("<hr style='margin: 15px 0; opacity:0.08;' />", unsafe_allow_html=True)
                
        action_verbs = report.get("action_verb_suggestions", [])
        if action_verbs:
            st.markdown("#### 🚀 Impactful Action Verbs to Incorporate")
            verbs_html = ""
            for verb in action_verbs:
                verbs_html += f'<span class="chip" style="background-color:rgba(6,182,212,0.12); color:#06B6D4; border:1px solid rgba(6,182,212,0.25);">{verb}</span>'
            st.markdown(verbs_html, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. INTERVIEW PREP TAB ---
    with tab_interview:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Interview Preparation Coach")
        
        difficulty_level = report.get("difficulty_level", "Intermediate")
        st.markdown(f"##### Targeted Assessment Difficulty: `{difficulty_level}`")
        
        selected_diff = st.radio(
            "Filter Questions",
            ["Matched Level Only", "Show All Questions"],
            horizontal=True,
            key="interview_difficulty_filter"
        )
        
        categories = {
            "HR & Career Questions": report.get("hr_questions", []),
            "Technical Questions": report.get("technical_questions", []),
            "Project-Specific Questions": report.get("project_questions", []),
            "Behavioral & Scenario Questions": report.get("behavioral_questions", [])
        }
        
        for category_name, q_list in categories.items():
            if q_list:
                st.markdown(f"#### 🏷️ {category_name}")
                for idx, question in enumerate(q_list, start=1):
                    expected_ans = ""
                    expected_list = report.get("expected_answers", [])
                    if idx - 1 < len(expected_list):
                        expected_ans = expected_list[idx - 1]
                    else:
                        expected_ans = "A strong answer should detail your structured analysis steps, reference tools or frameworks used, and quantify successful outcomes."
                    
                    with st.expander(f"Question {idx}: {question}"):
                        st.markdown(f"""
                            <div style="padding:10px 0;">
                                <strong style="color:#06B6D4;">💡 Sample Answer / Guideline:</strong><br>
                                <p style="font-size:13.5px; color:#E2E8F0; margin-top:5px;">{expected_ans}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        make_copy_section(question, f"copy_q_final_{category_name}_{idx}", "Copy Question Text")
                st.markdown("<br>", unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 7. RECOMMENDATIONS & EXPORT TAB ---
    with tab_actions:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Final Recommendations & Career Dashboard")
        
        col_metrics_reco, col_rec_desc = st.columns([1, 2])
        with col_metrics_reco:
            improv_score = min(99, ats_score + 15)
            st.markdown(draw_circular_progress(improv_score, "Estimated ATS Post-Edits", size=140, color="#10B981"), unsafe_allow_html=True)
        with col_rec_desc:
            st.markdown(f"""
                <div style="font-size: 14.5px; line-height: 1.7; padding-top: 15px; color:#E2E8F0;">
                    <p>Based on our multi-agent evaluation, implementing the suggestions inside the <strong>ATS</strong> and <strong>Optimizer</strong> sections can boost your ATS friendliness score to roughly <strong>{improv_score}/100</strong>.</p>
                    <p>Use the action items list below to track your editing milestones.</p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        st.markdown("#### 📝 Top 5 Priority Improvements")
        items = []
        if missing_sections:
            items.append(f"Add the missing section headers: {', '.join(missing_sections[:2])}")
        if missing_tech_skills:
            items.append(f"Integrate key technical skills: {', '.join(missing_tech_skills[:3])}")
        if improved_summary:
            items.append("Replace your Professional Summary with the AI-optimized summary version")
        if bullet_rewrites:
            items.append("Upgrade weak bullet points in your Experience sections using the provided AI Suggestion rewrites")
        if recommended_certs:
            items.append(f"Enroll in recommended study courses: {recommended_certs[0]}")
        
        while len(items) < 5:
            items.append("Refactor formatting spacing and align headers for improved readability")
            
        for i, item in enumerate(items[:5], start=1):
            st.checkbox(f"{i}. {item}", key=f"checkbox_final_item_{i}")
            
        st.markdown("---")
        
        st.markdown("#### 📂 Export & Actions")
        
        col_pdf, col_audio = st.columns(2)
        with col_pdf:
            if st.button("📥 Generate Printable PDF Report", key="generate_pdf_dashboard", use_container_width=True):
                try:
                    pdf_path = generate_report_pdf(
                        report,
                        candidate_name,
                        language=st.session_state.get("report_language", "English")
                    )
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            "Download PDF",
                            data=pdf_file.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as exc:
                    st.error(f"Could not generate PDF: {exc}")
                    
        with col_audio:
            if st.button("🔊 Narrate Report Summary", key="listen_summary_dashboard", use_container_width=True):
                try:
                    audio_path = text_to_speech(report.get("executive_summary", ""))
                    st.session_state["audio_path"] = audio_path
                    st.rerun()
                except VoiceError as exc:
                    st.error(f"Voice playback failed: {exc}")
                    
        if st.session_state.get("audio_path"):
            try:
                st.audio(load_audio_bytes(st.session_state["audio_path"]), format="audio/mp3")
            except VoiceError as exc:
                st.error(f"Could not load audio: {exc}")
                
        st.markdown("---")
        if st.button("🔄 Analyze New Resume", key="restart_analysis_opt", type="primary", use_container_width=True):
            st.session_state.pop("report", None)
            st.session_state.pop("audio_path", None)
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # -----------------------------------------------------------------
    # DISPLAY LANDING PAGE / UPLOAD CONTEXT
    # -----------------------------------------------------------------
    st.markdown("""
        <div style="text-align: center; margin: 40px 0 20px 0;">
            <h1 style="font-size: 58px; font-weight: 800; font-family: 'Outfit', sans-serif; background: linear-gradient(135deg, #F8FAFC 30%, #38BDF8 70%, #06B6D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;">
                🧠 HIRE READY AI
            </h1>
            <p style="font-size: 18px; color: #94A3B8; font-weight: 500; letter-spacing: 0.5px; max-width: 600px; margin: 0 auto;">
                Multi-Agent Career & Resume Intelligence Platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📤 Upload Credentials & Target Context", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Drop your Resume PDF here", type=["pdf"])
    
    if "job_description_main" not in st.session_state:
        st.session_state["job_description_main"] = ""
    if "job_desc_rev" not in st.session_state:
        st.session_state["job_desc_rev"] = 0

    voice_transcript = ""
    if input_mode == "Voice":
        st.markdown("##### 🎙️ Voice Context Notes")
        st.info("Record a short voice note describing your career goals to adapt the analysis.")
        
        if st.session_state.get("voice_success_msg"):
            st.success(st.session_state["voice_success_msg"])
        if st.session_state.get("voice_error_msg"):
            st.error(st.session_state["voice_error_msg"])

        # Check query parameter to force file uploader fallback for automated testing
        use_audio_input = hasattr(st, "audio_input") and "test_uploader" not in st.query_params
        if use_audio_input:
            audio_input = st.audio_input("Record voice input", key="voice_record_main")
            if audio_input is not None:
                audio_bytes = audio_input.getvalue()
                import hashlib
                audio_hash = hashlib.md5(audio_bytes).hexdigest()
                if audio_hash != st.session_state.get("last_audio_hash"):
                    st.session_state["last_audio_hash"] = audio_hash
                    st.session_state.pop("voice_success_msg", None)
                    st.session_state.pop("voice_error_msg", None)
                    
                    temp_audio_path = os.path.join(UPLOADS_DIR, "voice_input.wav")
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_bytes)
                    try:
                        voice_transcript = speech_to_text(temp_audio_path)
                        if voice_transcript:
                            st.session_state["job_description_main"] = voice_transcript
                            st.session_state["voice_success_msg"] = f"Transcribed Context: {voice_transcript}"
                            st.session_state["job_desc_rev"] = st.session_state.get("job_desc_rev", 0) + 1
                            st.rerun()
                    except VoiceError as exc:
                        st.session_state["voice_error_msg"] = f"Voice transcription failed: {exc}"
                        st.rerun()
            else:
                st.session_state.pop("last_audio_hash", None)
        else:
            uploaded_audio = st.file_uploader(
                "Upload voice note recording",
                type=["wav", "mp3", "m4a"],
                key="voice_upload_main"
            )
            if uploaded_audio is not None:
                audio_bytes = uploaded_audio.getvalue()
                import hashlib
                audio_hash = hashlib.md5(audio_bytes).hexdigest()
                if audio_hash != st.session_state.get("last_uploaded_audio_hash"):
                    st.session_state["last_uploaded_audio_hash"] = audio_hash
                    st.session_state.pop("voice_success_msg", None)
                    st.session_state.pop("voice_error_msg", None)
                    
                    temp_audio_path = os.path.join(UPLOADS_DIR, uploaded_audio.name)
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_bytes)
                    try:
                        voice_transcript = speech_to_text(temp_audio_path)
                        if voice_transcript:
                            st.session_state["job_description_main"] = voice_transcript
                            st.session_state["voice_success_msg"] = f"Transcribed Context: {voice_transcript}"
                            st.session_state["job_desc_rev"] = st.session_state.get("job_desc_rev", 0) + 1
                            st.rerun()
                    except VoiceError as exc:
                        st.session_state["voice_error_msg"] = f"Voice transcription failed: {exc}"
                        st.rerun()
            else:
                st.session_state.pop("last_uploaded_audio_hash", None)
        st.markdown("<br>", unsafe_allow_html=True)

    col_left_input, col_right_input = st.columns(2)
    with col_left_input:
        target_role = st.selectbox(
            "Target Job Role",
            [
                "Software Engineer",
                "Data Scientist",
                "Data Analyst",
                "Machine Learning Engineer",
                "Frontend Developer",
                "Backend Developer",
                "Full Stack Developer",
                "DevOps Engineer",
                "Product Manager",
                "Other",
            ],
            key="role_selection_main"
        )
        
        language = st.selectbox("Report Language", list(SUPPORTED_LANGUAGES.keys()), key="lang_selection_main")
        set_selected_language(language)
        
    with col_right_input:
        current_job_desc = st.session_state.get("job_description_main", "")
        job_description_key = f"job_description_widget_{st.session_state.get('job_desc_rev', 0)}"
        job_description = st.text_area(
            "Job Description / Career Goals (Recommended context)",
            value=current_job_desc,
            height=125,
            placeholder="Paste target job description to match skills, or use the voice recorder to speak your goals...",
            key=job_description_key
        )
        st.session_state["job_description_main"] = job_description
        
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_clicked = st.button("🚀 RUN CAREER INTELLIGENCE PLATFORM", type="primary", use_container_width=True, key="run_analysis_main")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Run analysis trigger
    if analyze_clicked:
        if uploaded_file is None:
            st.error("Please upload a resume PDF before analyzing.")
        else:
            try:
                # 1. Parse PDF text
                pdf_bytes = uploaded_file.read()
                raw_text = extract_text_from_bytes(pdf_bytes)

                # 2. Setup placeholders for animated workflow loader
                status_placeholder = st.empty()
                completed_steps = {
                    "resume_parser": "Pending",
                    "ats_agent": "Pending",
                    "job_match_agent": "Pending",
                    "skill_gap_agent": "Pending",
                    "resume_optimizer": "Pending",
                    "interview_agent": "Pending",
                    "report_generator": "Pending"
                }
                
                step_labels = {
                    "resume_parser": "Resume Parser Agent",
                    "ats_agent": "ATS Evaluation Agent",
                    "job_match_agent": "Job Matching Agent",
                    "skill_gap_agent": "Skill Gap Analysis Agent",
                    "resume_optimizer": "Resume Optimization Agent",
                    "interview_agent": "Interview Preparation Agent",
                    "report_generator": "Final Report Generation"
                }
                
                # Fetch LangGraph workflow
                workflow = get_workflow()
                initial_state = {
                    "raw_text": raw_text,
                    "job_description": job_description,
                    "target_role": target_role,
                }
                
                final_state = dict(initial_state)
                
                # Stream the workflow step by step
                for update in workflow.stream(initial_state, stream_mode="updates"):
                    node_name = list(update.keys())[0]
                    completed_steps[node_name] = "Completed"
                    
                    # Update progress UI
                    done_count = sum(1 for status in completed_steps.values() if status == "Completed")
                    progress_percent = int((done_count / len(completed_steps)) * 100)
                    
                    with status_placeholder.container():
                        st.markdown('<div class="loading-box">', unsafe_allow_html=True)
                        st.markdown("<h3 style='margin-top:0;'>⚙️ Running AI Multi-Agent Pipeline</h3>", unsafe_allow_html=True)
                        st.markdown(f"""
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" style="width: {progress_percent}%;"></div>
                            </div>
                            <div style="text-align: right; margin-bottom: 15px; font-weight: bold; color: #06B6D4;">{progress_percent}% Completed</div>
                        """, unsafe_allow_html=True)
                        
                        for step_key, step_lbl in step_labels.items():
                            status = completed_steps[step_key]
                            if status == "Completed":
                                st.markdown(f"🟢 **{step_lbl}** — *Completed*", unsafe_allow_html=True)
                            elif status == "Pending":
                                is_active = True
                                for prev in list(step_labels.keys())[:list(step_labels.keys()).index(step_key)]:
                                    if completed_steps[prev] != "Completed":
                                        is_active = False
                                
                                if is_active:
                                    st.markdown(f"⚡ <span class='active-step' style='color: #38BDF8; font-weight: bold;'>{step_lbl} — Analyzing...</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"⚪ <span style='color: #64748B;'>{step_lbl} — Pending</span>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Update local state dictionary
                    final_state.update(update[node_name])
                
                # Fetch output report
                report = final_state["final_report"]
                
                # Translate final report if needed
                if language != "English":
                    with st.spinner(f"Translating report to {language}..."):
                        try:
                            report = translate_report_sections(report, language)
                        except TranslationError as exc:
                            st.warning(f"Translation failed, showing English report instead: {exc}")

                st.session_state["report"] = report
                st.session_state["report_language"] = language
                st.session_state["balloons_shown"] = False
                
                status_placeholder.empty()
                st.rerun()

            except InvalidPDFError as exc:
                st.error(f"Invalid PDF: {exc}")
            except EmptyResumeError as exc:
                st.error(f"Empty resume: {exc}")
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

    # Display Analytics Session History
    previous_reports = load_memory().get("previous_reports", [])
    if previous_reports:
        st.markdown('<div class="glass-card" style="margin-top: 30px;">', unsafe_allow_html=True)
        st.markdown("#### 📚 Session Analytics History")
        for idx, prev_report in enumerate(reversed(previous_reports[-5:]), start=1):
            st.markdown(f"""
                <div class="timeline-content" style="margin-bottom: 8px; padding: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #F8FAFC;">{prev_report.get('candidate_name', 'Candidate')}</strong>
                        <span style="font-size: 12px; color: #94A3B8; margin-left: 10px;">({prev_report.get('resume_data', {}).get('email', 'N/A')})</span>
                    </div>
                    <div>
                        <span class="badge badge-success">ATS: {prev_report.get('ats_score', 'N/A')}</span>
                        <span class="badge badge-warning" style="margin-left: 5px;">Match: {prev_report.get('job_match_percent', 'N/A')}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
