""" app.py - Daily Reflection (chatbot mode) """
from __future__ import annotations
import html
from datetime import date, datetime
from typing import Any, TypedDict
import streamlit as st
from database import get_all_reflections, init_db, save_reflection
from llm import chat_reply, generate_summary

class Message(TypedDict):
    role: str
    content: str

class ReflectionFeedback(TypedDict):
    summary: str
    wins: str
    challenges: str
    focus: str

st.set_page_config(
    page_title="Pluto - Daily Reflection",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """ 
<style>
    .stApp { background-color: #0f0f0f; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stSidebar"] {
        background-color: #111 !important;
        border-right: 1px solid #1c1c1c !important;
    }
    [data-testid="stSidebar"] .stMarkdown p { color: #555 !important; font-size: 0.8rem; }
    .sidebar-logo { font-size: 1.2rem; font-weight: 700; color: #e0e0e0; letter-spacing: 0; margin-bottom: 0.15rem; }
    .sidebar-sub  { font-size: 0.75rem; color: #3a3a3a; margin-bottom: 2rem; }
    .page-title { font-size: 1.5rem; font-weight: 600; color: #e8e8e8; letter-spacing: 0; margin-bottom: 0.2rem; }
    .page-date  { font-size: 0.85rem; color: #444; margin-bottom: 1.5rem; }
    .bubble-wrap { display: flex; margin-bottom: 1.2rem; }
    .bubble-wrap.user { justify-content: flex-end; }
    .bubble-wrap.ai   { justify-content: flex-start; }
    .bubble {
        max-width: 65%;
        padding: 0.8rem 1.1rem;
        border-radius: 12px;
        font-size: 0.95rem;
        line-height: 1.5;
        white-space: pre-wrap;
    }
    .bubble.user { background: #2b3a5e; color: #e9ebef; border-bottom-right-radius: 2px; }
    .bubble.ai   { background: #1a1b20; color: #d0d4dc; border: 1px solid #2a2d3d; border-bottom-left-radius: 2px; }
    .result-card  { background: #141414; border: 1px solid #212121; border-radius: 10px; padding: 1.1rem 1.4rem; margin-bottom: 0.9rem; }
    .result-label { font-size: 0.68rem; font-weight: 700; color: #6b8cff; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.55rem; }
    .result-text  { font-size: 0.9rem; color: #c0c0c0; line-height: 1.7; white-space: pre-wrap; }
    .saved-banner { background: #0d1a0d; border: 1px solid #1a3a1a; border-radius: 8px; padding: 0.6rem 1rem; color: #4caf50; font-size: 0.85rem; margin-bottom: 1.2rem; }
</style> 
""",
    unsafe_allow_html=True,
)

def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "phase" not in st.session_state:
        st.session_state.phase = "start"
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "saved" not in st.session_state:
        st.session_state.saved = False

def count_user_messages() -> int:
    messages: list[Message] = st.session_state.messages
    return sum(1 for message in messages if message["role"] == "user")

def render_message(role: str, content: str) -> None:
    css = "user" if role == "user" else "ai"
    safe_content = html.escape(content)
    st.markdown(
        f'<div class="bubble-wrap {css}"><div class="bubble {css}">{safe_content}</div></div>',
        unsafe_allow_html=True,
    )

def render_result_card(label: str, text: str, extra_style: str = "") -> None:
    st.markdown(
        f"""
        <div class="result-card" style="{extra_style}">
            <div class="result-label">{html.escape(label)}</div>
            <div class="result-text">{html.escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def add_user_message(final_text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": final_text})
    if final_text.lower() in ("done", "generate", "summarize", "finish", "end"):
        st.session_state.phase = "generating"
        return
    with st.spinner("Thinking..."):
        reply = chat_reply(st.session_state.messages)
    if reply == "[END_REFLECTION]":
        # Stay in chat phase — just add a closing message and keep the input open
        st.session_state.messages.append({
            "role": "assistant",
            "content": "That's everything I need. Go ahead and generate your reflection whenever you're ready."
        })
        st.session_state.phase = "chat"
    elif reply:
        st.session_state.messages.append({"role": "assistant", "content": reply})

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">Pluto</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Daily reflection</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Reflection")
        st.page_link("pages/history.py", label="History")
        st.page_link("pages/insights.py", label="Insights")
        st.markdown("---")
        init_db()
        count = len(get_all_reflections())
        suffix = "s" if count != 1 else ""
        st.markdown(f"<p>{count} reflection{suffix} saved</p>", unsafe_allow_html=True)

def render_chat_phase() -> None:
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])
    if count_user_messages() >= 3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate Reflection", type="primary"):
            st.session_state.phase = "generating"
            st.rerun()
            
    placeholder = "Type your reply..."
    user_input = st.chat_input(placeholder)
    if user_input:
        add_user_message(user_input.strip())
        st.rerun()

def render_generating_phase() -> None:
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])
    st.markdown("<br>", unsafe_allow_html=True)
    with st.spinner("Generating your reflection..."):
        try:
            feedback: ReflectionFeedback = generate_summary(st.session_state.messages)
            st.session_state.feedback = feedback
            st.session_state.phase = "result"
        except Exception as exc:
            st.error(f"Something went wrong: {exc}\n\nMake sure Ollama is running (`ollama serve`).")
            st.session_state.phase = "chat"
    st.rerun()

def save_current_reflection(feedback: ReflectionFeedback) -> None:
    if st.session_state.saved:
        return
    user_messages = [
        message["content"]
        for message in st.session_state.messages
        if message["role"] == "user"
    ]
    save_reflection(
        date=datetime.now().isoformat(),
        responses={"conversation": "\n".join(user_messages)},
        summary=feedback["summary"],
        wins=feedback["wins"],
        challenges=feedback["challenges"],
        focus=feedback["focus"],
    )
    st.session_state.saved = True

def render_result_phase() -> None:
    feedback: ReflectionFeedback | None = st.session_state.feedback
    if not feedback:
        return
    save_current_reflection(feedback)
    with st.expander("View conversation", expanded=False):
        for message in st.session_state.messages:
            render_message(message["role"], message["content"])
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Messages Shared", count_user_messages())
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="saved-banner">Reflection saved</div>', unsafe_allow_html=True)
    render_result_card("Daily Summary", feedback["summary"])
    first_column, second_column = st.columns(2)
    with first_column:
        render_result_card("Wins", feedback["wins"])
    with second_column:
        render_result_card("Challenges", feedback["challenges"])
    render_result_card("Tomorrow's Focus", feedback["focus"], "border-left: 3px solid #6b8cff;")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Start a new reflection"):
        for key in ["messages", "phase", "feedback", "saved"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

render_sidebar()
init_session_state()

st.markdown('<div class="page-title">Daily Reflection</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="page-date">{date.today().strftime("%A, %B %d, %Y")}</div>',
    unsafe_allow_html=True,
)

if st.session_state.phase == "start":
    opening = "What did you work on today?"
    st.session_state.messages.append({"role": "assistant", "content": opening})
    st.session_state.phase = "chat"
    st.rerun()

if st.session_state.phase == "chat":
    render_chat_phase()

if st.session_state.phase == "generating":
    render_generating_phase()

if st.session_state.phase == "result":
    render_result_phase()