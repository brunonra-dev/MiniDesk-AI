import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import database


class DatabaseTests(unittest.TestCase):
    def test_initialization_creates_schema_and_preserves_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            with patch.object(database, "DB_PATH", path):
                database.init_db()
                self.assertTrue(path.is_file())
                with closing(sqlite3.connect(path)) as connection:
                    columns = connection.execute("PRAGMA table_info(tickets)").fetchall()
                    self.assertEqual(
                        [(column[1], column[2]) for column in columns],
                        [("id", "INTEGER"), ("description", "TEXT"),
                         ("category", "TEXT"), ("priority", "TEXT"),
                         ("summary", "TEXT")],
                    )
                    self.assertEqual(columns[0][5], 1)
                    connection.execute(
                        "INSERT INTO tickets (description) VALUES (?)", ("Prueba",)
                    )
                    connection.commit()

                database.init_db()
                with closing(sqlite3.connect(path)) as connection:
                    self.assertEqual(
                        connection.execute("SELECT * FROM tickets").fetchall(),
                        [(1, "Prueba", None, None, None)],
                    )
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute("INSERT INTO tickets (description) VALUES (NULL)")


if __name__ == "__main__":
    unittest.main()
