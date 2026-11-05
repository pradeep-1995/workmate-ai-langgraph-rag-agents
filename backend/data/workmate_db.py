
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Resolve the project-relative database location
DB_PATH = Path(__file__).resolve().with_name("workmate.db")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    # Ensure the containing directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium'
                    CHECK(priority IN ('low', 'medium', 'high')),
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending', 'completed')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)



if __name__ == "__main__":
    print(f"Database initialized at: {DB_PATH}")
