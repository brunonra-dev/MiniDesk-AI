import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "minidesk.db"


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                category TEXT,
                priority TEXT,
                summary TEXT
            )
        """)
        connection.commit()


def create_ticket(description: str) -> dict:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "INSERT INTO tickets (description) VALUES (?)", (description,)
        )
        ticket = connection.execute(
            "SELECT id, description, category, priority, summary FROM tickets WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        connection.commit()
        return dict(ticket)


def list_tickets() -> list[dict]:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, description, category, priority, summary FROM tickets ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print(f"Base inicializada: {DB_PATH}")
