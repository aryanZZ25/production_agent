"""
database.py — Handles all SQLite database operations.

This module creates the database, saves reflections, and retrieves them.
It's intentionally simple: one table, a few functions, no ORM.
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "reflections.db"


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Makes rows behave like dicts
    return conn


def init_db():
    """Create the reflections table if it doesn't already exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reflections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            responses   TEXT NOT NULL,   -- JSON: user's raw answers
            summary     TEXT NOT NULL,   -- AI-generated summary
            wins        TEXT NOT NULL,   -- AI-generated wins
            challenges  TEXT NOT NULL,   -- AI-generated challenges
            focus       TEXT NOT NULL,   -- AI-generated tomorrow focus
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_reflection(date: str, responses: dict, summary: str, wins: str, challenges: str, focus: str):
    """
    Save a completed reflection to the database.

    Args:
        date: The date string (e.g. '2025-06-21')
        responses: Dict of user answers to the 4 questions
        summary: AI-generated daily summary paragraph
        wins: AI-generated wins bullet points
        challenges: AI-generated challenges bullet points
        focus: AI-generated tomorrow focus statement
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO reflections (date, responses, summary, wins, challenges, focus, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            date,
            json.dumps(responses),       # store dict as json string
            summary,
            wins,
            challenges,
            focus,
            datetime.now().isoformat(),  # simestamp for ordering
        ),
    )
    conn.commit()
    conn.close()


def get_all_reflections() -> list[dict]:
    """
    Fetch all reflections from the database, newest first.

    Returns:
        A list of dicts with all reflection fields.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reflections ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        entry = dict(row)
        entry["responses"] = json.loads(entry["responses"])  # parse json back to dict
        result.append(entry)
    return result


def get_reflection_count() -> int:
    """Return the total number of saved reflections."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM reflections").fetchone()[0]
    conn.close()
    return count

def delete_reflection(reflection_id: int) -> None:
    """Delete a reflection from the database by its ID."""
    conn = get_connection()
    conn.execute("DELETE FROM reflections WHERE id = ?", (reflection_id,))
    conn.commit()
    conn.close()
