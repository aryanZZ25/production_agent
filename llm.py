"""
llm.py — All AI/LLM logic lives here.

Three functions:
  1. chat_reply()       — AI responds to the user in a conversation and asks follow-ups
  2. generate_summary() — AI reads the full chat and produces the structured reflection
  3. generate_insights()— AI analyzes historical reflections for patterns

Uses Groq API (llama-3.1-8b-instant).
Set GROQ_API_KEY in your .env file.
"""

import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

chat_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4,
    api_key=os.getenv("GROQ_API_KEY"),
)

summary_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY"),
)

# Short/negative answers — never follow up on these, just move on
SHORT_ANSWERS = {
    "no", "nope", "nah", "nothing", "none", "not really", "n/a",
    "not much", "i didn't", "i did not", "no issues", "no blockers",
    "i don't know", "idk", "i dont know", "no work", "i did not work",
    "i did no work", "lack of tasks", "no tasks", "nothing new",
}

def _is_short_answer(text: str) -> bool:
    cleaned = text.lower().strip().rstrip(".,!?")
    return cleaned in SHORT_ANSWERS or len(cleaned.split()) <= 3


def chat_reply(history: list[dict]) -> str:
    """
    Standup flow — Python owns topic order and follow-up eligibility,
    Llama handles phrasing and decides whether to follow up on substantive answers.

    Topics:
      1. What they worked on today
      2. Blockers / issues
      3. What they learned
      4. Tomorrow's priority

    Follow-up rules:
      - NEVER follow up on short/negative answers ("no", "nope", "nothing", etc.)
      - Only follow up if the answer is substantive and genuinely needs clarification
      - Max ONE follow-up per topic
    """

    if len(history) == 0:
        return "Hey — quick standup. What did you work on today?"

    user_messages  = [m for m in history if m["role"] == "user"]
    assistant_msgs = [m for m in history if m["role"] == "assistant"]
    user_count     = len(user_messages)

    if user_count >= 8:
        return "[END_REFLECTION]"

    last_user = user_messages[-1]["content"].strip()

    # Topics in order
    TOPICS = [
        "What did you work on today?",
        "Did anything slow you down today?",
        "Did you pick up anything new while working?",
        "What's your top priority for tomorrow?",
    ]

    # Infer current topic by scanning assistant messages for topic text
    current_topic = 0
    for msg in assistant_msgs:
        text = msg["content"].strip()
        for i, q in enumerate(TOPICS):
            # Match by the core keyword of each topic question
            if q.lower()[:20] in text.lower():
                current_topic = i

    # Count assistant turns since current topic question was asked
    topic_start_idx = 0
    for i, msg in enumerate(assistant_msgs):
        if TOPICS[current_topic].lower()[:20] in msg["content"].lower():
            topic_start_idx = i

    turns_on_topic = len(assistant_msgs) - topic_start_idx
    follow_up_used = turns_on_topic >= 2

    # Move to next topic if follow-up already used OR answer is short/negative
    should_advance = follow_up_used or _is_short_answer(last_user)

    next_topic_idx = current_topic + 1

    if should_advance:
        if next_topic_idx >= len(TOPICS):
            return "[END_REFLECTION]"
        next_question = TOPICS[next_topic_idx]
    else:
        # Llama will decide: follow up or advance
        next_question = TOPICS[next_topic_idx] if next_topic_idx < len(TOPICS) else None

    # Build transcript
    conversation = "\n".join(
        f'{"Engineer" if m["role"] == "assistant" else "Dev"}: {m["content"]}'
        for m in history
    )

    # ── Case 1: must advance to next topic ───────────────────────────
    if should_advance:
        prompt = f"""You are a strict senior engineer running a daily standup. You are direct and professional, not friendly or warm.

Conversation so far:
{conversation}

Ask this next standup question in one short sentence (under 15 words):
{next_question}

Do not acknowledge what they said. Do not explain anything. Just ask the question.
Reply:"""

    # ── Case 2: Llama decides follow-up or advance ───────────────────
    else:
        advance_q = next_question if next_question else "Standup complete."
        prompt = f"""You are a strict senior engineer running a daily standup. You are direct and blunt, not warm or encouraging.

Conversation so far:
{conversation}

The dev just gave a substantive answer. Decide:

Option A — Ask ONE short follow-up if something specific is unclear or worth understanding better.
Option B — Skip follow-up and ask the next standup question: "{advance_q}"

Rules:
- Never follow up on "no", "nope", "nothing", "not really" or any short negative answer
- Only follow up if the answer has actual content worth digging into
- Follow-up must be under 15 words
- Do not begin with "Got it", "Okay", "Nice", "Great", "Understood", or any filler
- Do not explain your choice — just reply with the question

Reply:"""

    response = chat_llm.invoke(prompt).content.strip()

    for prefix in ("reply:", "engineer:", "assistant:", "ai:"):
        if response.lower().startswith(prefix):
            response = response[len(prefix):].strip()

    if not response or len(response) > 200:
        return next_question or "[END_REFLECTION]"

    return response


def generate_summary(history: list[dict]) -> dict:
    """
    Reads the entire chat conversation and produces a structured daily reflection.

    Returns:
        {
            "summary":    "...",
            "wins":       "...",
            "challenges": "...",
            "focus":      "..."
        }
    """

    user_responses = "\n".join(
        f"- {msg['content']}"
        for msg in history
        if msg["role"] == "user"
    )

    prompt = f"""You are a productivity coach. Below are a user's responses from their daily standup.

USER'S RESPONSES:
{user_responses}

Your entire response must contain ONLY these four XML tags and nothing outside them.

<summary>
Write 2-3 sentences directly addressing the user as "you".
Be encouraging but realistic.
Only use information the user explicitly mentioned. Do not invent anything.
</summary>

<wins>
Write exactly 2-3 bullet points starting with "- ".
Only use information the user explicitly mentioned.
If no wins were mentioned: - No clear wins were mentioned today.
</wins>

<challenges>
Write exactly 2-3 bullet points starting with "- ".
Only use information the user explicitly mentioned.
If no challenges were mentioned: - No major challenges were mentioned today.
</challenges>

<focus>
Write 1-2 sentences on what the user should focus on tomorrow.
If they mentioned a goal, build on it. If not, suggest a practical next step based on today.
</focus>"""

    raw = summary_llm.invoke(prompt).content
    return _parse_tagged_output(raw)


def generate_insights(reflections: list[dict]) -> str:
    """
    Analyzes all stored reflections and returns a plain-text insight report.
    """

    if not reflections:
        return "No reflections yet. Start your first daily reflection to see insights here."

    summary_text = ""
    for r in reflections[-10:]:
        summary_text += f"""
Date: {r['date']}
Summary: {r.get('summary', '')}
Wins: {r.get('wins', '')}
Challenges: {r.get('challenges', '')}
Focus: {r.get('focus', '')}
---"""

    prompt = f"""You are a productivity analyst. Read these daily reflections and identify patterns.

REFLECTIONS:
{summary_text}

Write your analysis using exactly these section headers:

COMMON CHALLENGES:
List 2-3 recurring difficulties you notice across the reflections.

COMMON ACHIEVEMENTS:
List 2-3 types of wins that keep appearing.

RECURRING GOALS:
List themes or goals that come up repeatedly.

PERSONALIZED RECOMMENDATIONS:
Give 3 specific, actionable suggestions based on the patterns above. Be direct — not generic advice.

Keep the tone honest and practical."""

    return summary_llm.invoke(prompt).content


def _parse_tagged_output(text: str) -> dict:
    """Extract content between <tag> and </tag> from AI output."""
    import re

    def extract(tag: str) -> str:
        match = re.search(
            rf"<{tag}\s*>(.*?)</{tag}\s*>",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        return f"(Could not parse {tag} — try generating again)"

    return {
        "summary":    extract("summary"),
        "wins":       extract("wins"),
        "challenges": extract("challenges"),
        "focus":      extract("focus"),
    }