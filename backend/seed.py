import sqlite3
from contextlib import closing

import database

SAMPLE_DESCRIPTIONS = (
    "No puedo acceder al correo ni enviar mensajes. Estoy bloqueado para trabajar y necesito ayuda urgente.",
    "La impresora de la oficina imprime con rayas. Puedo usar otra mientras revisan el problema.",
    "Necesito que me expliquen cómo configurar la firma del correo. No es urgente.",
    "Una factura vence hoy y falta la aprobación del pago. Necesito resolverlo con urgencia.",
    "Quiero saber qué documentación presentar para solicitar el reintegro de un gasto. No hay urgencia.",
    "Propongo organizar un intercambio de libros entre compañeros el próximo mes. ¿Podemos coordinarlo?",
)


def seed_tickets() -> int:
    database.init_db()
    with closing(sqlite3.connect(database.DB_PATH)) as connection:
        connection.executemany(
            """
            INSERT INTO tickets (description)
            SELECT ?
            WHERE NOT EXISTS (SELECT 1 FROM tickets WHERE description = ?)
            """,
            [(description, description) for description in SAMPLE_DESCRIPTIONS],
        )
        connection.commit()
        return connection.total_changes


if __name__ == "__main__":
    added = seed_tickets()
    print(f"Tickets de ejemplo agregados: {added}. Base: {database.DB_PATH}")
