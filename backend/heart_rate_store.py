"""
SQLite-backed store for heart-rate readings pushed by a paired smartwatch
(Galaxy Watch via Health Connect on Android, Apple Watch via HealthKit on
iOS). The web client has no direct watch access, so it only ever reads
what a phone app has already synced here.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "users.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS heart_rate_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bpm REAL NOT NULL,
            source TEXT NOT NULL,
            measured_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def record_heart_rate(name, bpm, source="watch"):
    measured_at = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO heart_rate_records (name, bpm, source, measured_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, bpm, source, measured_at),
    )
    conn.commit()
    conn.close()

    return {"bpm": bpm, "source": source, "measured_at": measured_at}


def get_latest(name):
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT bpm, source, measured_at FROM heart_rate_records
        WHERE name = ? ORDER BY measured_at DESC LIMIT 1
        """,
        (name,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_history(name, limit=20):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT bpm, source, measured_at FROM heart_rate_records
        WHERE name = ? ORDER BY measured_at DESC LIMIT ?
        """,
        (name, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_records(name):
    conn = get_db_connection()
    conn.execute("DELETE FROM heart_rate_records WHERE name = ?", (name,))
    conn.commit()
    conn.close()
