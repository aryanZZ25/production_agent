# Pluto — AI Daily Standup Agent

A conversational AI that runs your daily standup, captures blockers and wins, and generates a structured reflection — stored locally.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.1-00A67E?style=flat)
![SQLite](https://img.shields.io/badge/SQLite-local--first-003B57?style=flat&logo=sqlite&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b-F55036?style=flat)
![License](https://img.shields.io/badge/License-MIT-gray?style=flat)

---

## Overview

Pluto is a local-first AI standup agent for developers who want a structured daily reflection habit without the overhead of a full productivity suite.

Instead of a blank journal or a clunky form, Pluto walks you through five focused standup questions, asks clarifying follow-ups via an LLM, and generates a clean written reflection — saved to a local SQLite database.

---

## Features

| | |
|---|---|
| Guided standup flow | Fixed 5-question format: work → progress → blockers → learnings → tomorrow |
| AI follow-ups | LLM asks smart clarifying questions based on your answers |
| Auto reflection | Generates a structured daily summary when the standup ends |
| Local persistence | All reflections saved to SQLite — no cloud, no accounts |
| Environment config | API keys managed via `.env` |

---

## Quick start

**1. Clone the repo**

```bash
git clone https://github.com/aryanZZ25/productivity-agent.git
cd productivity-agent
```

**2. Create a virtual environment**

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows
python -m venv .venv && .venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_api_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

**5. Run**

```bash
python app.py
```

---

## Example session

```
What did you work on today?
> Integrated Groq LLM into the standup flow.

Was this a new integration or building on existing work?
> New — replaced the previous OpenAI setup.

Did anything block you today?
> Spent an hour debugging token limits.

Did you learn anything new?
> Learned how to manage context windows efficiently.

What's your top priority for tomorrow?
> Add reflection history to the UI.

Generating reflection...

Productive session. Migrated the LLM backend from OpenAI to Groq,
achieving notably lower latency. A debugging detour on token limits
turned into a useful lesson in context window management.
Tomorrow: bring reflection history into the UI.

Reflection saved — June 26 2025
```

---

## Project structure

```
productivity-agent/
├── app.py          — standup flow orchestration
├── llm.py          — follow-ups and reflection generation
├── database.py     — SQLite setup and storage
├── pages/          — history and settings views
├── test.py
├── .env.example
├── requirements.txt
└── .gitignore
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| LLM backend | Groq (`llama-3.1-8b-instant`) via LangChain |
| Persistence | SQLite, auto-created on first run |
| UI | Streamlit |
| Config | python-dotenv |

---

## Database schema

```sql
CREATE TABLE reflections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,
    answers     TEXT NOT NULL,    -- JSON of standup Q&A
    summary     TEXT NOT NULL,    -- AI-generated reflection
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

The database file (`pluto.db`) is excluded from version control via `.gitignore`.

---

## Roadmap

- [x] 5-question standup flow
- [x] LLM-powered clarifying follow-ups
- [x] AI-generated daily reflection
- [x] SQLite persistence
- [ ] Reflection history dashboard
- [ ] Voice input via WhisperLive
- [ ] Weekly and monthly summaries
- [ ] Export reflections as PDF
- [ ] Analytics and streak tracking

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m "feat: describe change"`
4. Push and open a pull request

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Aryan Zinge**  
Computer Engineering Student · AI and Full-Stack Engineering  
[github.com/aryanZZ25](https://github.com/aryanZZ25)
