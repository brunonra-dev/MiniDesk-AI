import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import seed


class SeedTests(unittest.TestCase):
    def test_seed_preserves_existing_tickets_and_does_not_duplicate_samples(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(database, "DB_PATH", Path(directory) / "test.db"):
                database.init_db()
                existing = database.create_ticket(seed.SAMPLE_DESCRIPTIONS[0])
                analyzed = database.update_analysis(
                    existing["id"], "soporte", "alta", "Resumen conservado."
                )
                custom = database.create_ticket("Una solicitud propia del usuario.")

                self.assertEqual(seed.seed_tickets(), len(seed.SAMPLE_DESCRIPTIONS) - 1)
                rows = database.list_tickets()
                self.assertEqual(len(rows), len(seed.SAMPLE_DESCRIPTIONS) + 1)
                self.assertEqual(database.get_ticket(existing["id"]), analyzed)
                self.assertEqual(database.get_ticket(custom["id"]), custom)
                for row in rows:
                    if row["id"] not in (existing["id"], custom["id"]):
                        self.assertEqual(
                            (row["category"], row["priority"], row["summary"]),
                            (None, None, None),
                        )

                self.assertEqual(seed.seed_tickets(), 0)
                self.assertEqual(database.list_tickets(), rows)


if __name__ == "__main__":
    unittest.main()
