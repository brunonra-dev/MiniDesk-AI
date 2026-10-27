import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

import database
from main import TicketCreate


class TicketDatabaseTests(unittest.TestCase):
    def test_create_and_list_ticket_preserves_text_as_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.db"
            description = "Revisar '); DROP TABLE tickets; --"

            with patch.object(database, "DB_PATH", path):
                database.init_db()
                created = database.create_ticket(description)
                tickets = database.list_tickets()

                self.assertEqual(
                    created,
                    {
                        "id": 1,
                        "description": description,
                        "category": None,
                        "priority": None,
                        "summary": None,
                    },
                )
                self.assertEqual(tickets, [created])

                with closing(sqlite3.connect(path)) as connection:
                    self.assertEqual(
                        connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0],
                        1,
                    )


class TicketValidationTests(unittest.TestCase):
    def test_description_is_required_nonempty_and_limited(self):
        for value in (None, 42, "", "   ", "x" * 5001):
            with self.assertRaises(ValidationError):
                TicketCreate(description=value)

        with self.assertRaises(ValidationError):
            TicketCreate()

        self.assertEqual(TicketCreate(description="  Acceso bloqueado  ").description, "Acceso bloqueado")

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            TicketCreate(description="Acceso bloqueado", priority="alta")


if __name__ == "__main__":
    unittest.main()
