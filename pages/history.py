"""
pages/history.py — The History page.

Shows all past reflections in reverse chronological order.
Each entry is displayed in a collapsible expander for clean browsing.
"""

import streamlit as st
import sys
import os

# Add the parent directory to path so we can import database.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_all_reflections, init_db, delete_reflection

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="History · Pluto",
    page_icon="📋",
    layout="wide",
)

# ── Minimal dark styling ──────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; }

    .page-title {
        font-size: 1.6rem;
        font-weight: 600;
        color: #e8e8e8;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .page-subtitle {
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 2rem;
    }

    /* Card container for each reflection */
    .ref-card {
        background: #161616;
        border: 1px solid #242424;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .ref-date {
        font-size: 0.78rem;
        color: #888;
        font-weight: 500;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .ref-summary {
        font-size: 0.95rem;
        color: #ccc;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    /* Section label inside expanded view */
    .section-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b8cff;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 1rem;
        margin-bottom: 0.35rem;
    }
    .section-content {
        font-size: 0.9rem;
        color: #aaa;
        line-height: 1.65;
    }

    /* Answers from the user */
    .answer-label {
        font-size: 0.72rem;
        color: #555;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.8rem;
        margin-bottom: 0.2rem;
    }
    .answer-text {
        font-size: 0.88rem;
        color: #888;
        line-height: 1.5;
        font-style: italic;
    }

    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #444;
    }
    .empty-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .empty-text {
        font-size: 1rem;
        color: #555;
    }
    .empty-hint {
        font-size: 0.85rem;
        color: #3a3a3a;
        margin-top: 0.4rem;
    }

    /* Override streamlit expander styling */
    .streamlit-expanderHeader {
        background: #1a1a1a !important;
        border-radius: 6px !important;
        color: #aaa !important;
        font-size: 0.82rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────

st.markdown('<div class="page-title">Reflection History</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">A record of your daily reflections</div>', unsafe_allow_html=True)

# Ensure the database table exists
init_db()

reflections = get_all_reflections()

if not reflections:
    # Show a friendly empty state
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-text">No reflections yet</div>
        <div class="empty-hint">Complete your first daily reflection to see it here.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"**{len(reflections)}** reflection{'s' if len(reflections) != 1 else ''} saved")
    st.markdown("---")

    for r in reflections:
        # Build a readable date label (e.g. "June 21, 2025")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(r["date"])
            label = dt.strftime("%B %d, %Y • %I:%M %p")
        except Exception:
            label = r["date"]

        # Each reflection gets its own card-style expander
        with st.expander(f"📅  {label}", expanded=False):

            # AI-generated summary at the top
            st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="section-content">{r["summary"]}</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="section-label">Wins</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-content">{r["wins"]}</div>', unsafe_allow_html=True)

                st.markdown('<div class="section-label">Tomorrow\'s Focus</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-content">{r["focus"]}</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="section-label">Challenges</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-content">{r["challenges"]}</div>', unsafe_allow_html=True)

            # Show the raw conversation the user had
            st.markdown("---")
            st.markdown('<div class="section-label">Your Responses</div>', unsafe_allow_html=True)
            resp = r["responses"]
            conversation = resp.get("conversation", "—")
            st.markdown(f'<div class="answer-text">{conversation}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete this entry", key=f"delete_{r['id']}"):
                delete_reflection(r['id'])
                st.rerun()