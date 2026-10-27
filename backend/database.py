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


if __name__ == "__main__":
    init_db()
    print(f"Base inicializada: {DB_PATH}")
