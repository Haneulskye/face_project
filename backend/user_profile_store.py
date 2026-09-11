"""
SQLite-backed store for real app-user profiles (name, age, nickname,
gender, height, weight). Kept separate from the `iris_users` table
already present in users.db so the two stay independent.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "users.db"

MINIMUM_AGE = 14


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_users (
            name TEXT PRIMARY KEY,
            age INTEGER,
            gender TEXT,
            height_cm REAL,
            weight_kg REAL,
            note TEXT,
            registered_at TEXT NOT NULL
        )
        """
    )

    # Migration: add `nickname` to databases created before this column existed.
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(app_users)")
    }
    if "nickname" not in existing_columns:
        conn.execute("ALTER TABLE app_users ADD COLUMN nickname TEXT")

    conn.commit()
    conn.close()


def user_exists(name):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT 1 FROM app_users WHERE name = ?", (name,)
    ).fetchone()
    conn.close()
    return row is not None


def create_user(name, age, nickname, gender, height_cm, weight_kg, note=""):
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO app_users
            (name, age, nickname, gender, height_cm, weight_kg, note, registered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            age,
            nickname,
            gender,
            height_cm,
            weight_kg,
            note,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_user(name):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM app_users WHERE name = ?", (name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
