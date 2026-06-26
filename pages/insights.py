"""
pages/insights.py — The Insights page.

Fetches all stored reflections and uses the AI to identify patterns:
  - Common challenges
  - Common achievements
  - Recurring goals
  - Personalized recommendations
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_all_reflections, init_db
from llm import generate_insights

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Insights · Pluto",
    page_icon="📈",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; }

    .page-title {
        font-size: 1.6rem;
        font-weight: 600;
        color: #e8e8e8;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .page-subtitle {
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 2rem;
    }

    /* Individual insight section cards */
    .insight-card {
        background: #141414;
        border: 1px solid #222;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.85rem;
    }
    .insight-card.recommendations {
        border-left: 3px solid #6b8cff;
    }
    .insight-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #6b8cff;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }
    .insight-body {
        font-size: 0.9rem;
        color: #bbb;
        line-height: 1.75;
        white-space: pre-wrap;
    }

    /* Stats row at the top */
    .stat-card {
        background: #161616;
        border: 1px solid #222;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #6b8cff;
        letter-spacing: -0.03em;
    }
    .stat-label {
        font-size: 0.75rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.2rem;
    }

    /* Generate button */
    .stButton > button {
        background: #6b8cff !important;
        color: #fff !important;
        border: none !important;
        border-radius: 7px !important;
        padding: 0.55rem 1.6rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: opacity 0.15s !important;
    }
    .stButton > button:hover {
        opacity: 0.85 !important;
    }

    .not-enough {
        background: #161616;
        border: 1px solid #222;
        border-radius: 10px;
        padding: 2.5rem;
        text-align: center;
        color: #555;
        font-size: 0.9rem;
    }
    .not-enough span {
        display: block;
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────

st.markdown('<div class="page-title">Insights</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Patterns and recommendations based on your reflection history</div>', unsafe_allow_html=True)

init_db()
reflections = get_all_reflections()
count = len(reflections)

# ── Stats strip ───────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{count}</div>
        <div class="stat-label">Total Reflections</div>
    </div>""", unsafe_allow_html=True)

with col2:
    # Days since first reflection
    if count > 0:
        from datetime import datetime
        try:
            first_date = datetime.fromisoformat(reflections[-1]["date"])
            days = (datetime.today() - first_date).days + 1
        except Exception:
            days = "—"
    else:
        days = 0
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{days}</div>
        <div class="stat-label">Days Tracked</div>
    </div>""", unsafe_allow_html=True)

with col3:
    # Simple streak: count consecutive days from today
    streak = 0
    if count > 0:
        from datetime import datetime, timedelta
        dates = set()
        for r in reflections:
            try:
                dates.add(datetime.fromisoformat(r["date"]).date())
            except Exception:
                pass
        check = datetime.today().date()
        while check in dates:
            streak += 1
            check -= timedelta(days=1)

    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{streak}</div>
        <div class="stat-label">Day Streak</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Minimum reflections gate ──────────────────────────────────────────────────

MIN_REFLECTIONS = 2  # Need at least a couple to find patterns

if count < MIN_REFLECTIONS:
    st.markdown(f"""
    <div class="not-enough">
        <span>🔍</span>
        You need at least {MIN_REFLECTIONS} reflections to generate insights.<br>
        You have {count} so far — keep reflecting daily!
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Insights generator ────────────────────────────────────────────────────

    st.markdown("**Analyze your last 10 reflections to surface patterns and recommendations.**")
    st.markdown("")

    if st.button("Generate Insights", use_container_width=False):
        with st.spinner("Analyzing your reflections…"):
            try:
                insights_text = generate_insights(reflections)
                # Store in session state so it persists without re-running the LLM
                st.session_state["insights"] = insights_text
            except Exception as e:
                st.error(f"Could not generate insights: {e}")

    # Show cached insights if available
    if "insights" in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)

        raw = st.session_state["insights"]

        # ── Parse the four sections out of the AI's plain-text output ──
        # The LLM is prompted to use these exact headers, so we split on them.
        SECTIONS = [
            ("COMMON CHALLENGES",       "Common Challenges",        ""),
            ("COMMON ACHIEVEMENTS",     "Common Achievements",      ""),
            ("RECURRING GOALS",         "Recurring Goals",          ""),
            ("PERSONALIZED RECOMMENDATIONS", "Recommendations",     "recommendations"),
        ]

        def extract_section(text: str, header: str, next_headers: list[str]) -> str:
            """Pull text between `header:` and the next known header."""
            start_marker = header + ":"
            start = text.find(start_marker)
            if start == -1:
                return ""
            start += len(start_marker)
            end = len(text)
            for nxt in next_headers:
                pos = text.find(nxt + ":", start)
                if pos != -1:
                    end = min(end, pos)
            return text[start:end].strip()

        all_headers = [s[0] for s in SECTIONS]

        for header, display_label, extra_class in SECTIONS:
            other_headers = [h for h in all_headers if h != header]
            body = extract_section(raw, header, other_headers)
            if body:
                st.markdown(f"""
                <div class="insight-card {extra_class}">
                    <div class="insight-label">{display_label}</div>
                    <div class="insight-body">{body}</div>
                </div>""", unsafe_allow_html=True)

        # Fallback: if parsing found nothing, show raw output
        if not any(extract_section(raw, h, [s[0] for s in SECTIONS if s[0] != h]) for h, _, _ in SECTIONS):
            st.markdown(f'<div class="insight-card"><div class="insight-body">{raw}</div></div>', unsafe_allow_html=True)

        # Button to clear and regenerate
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Refresh Analysis"):
            del st.session_state["insights"]
            st.rerun()