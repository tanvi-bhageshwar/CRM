"""
Database layer.

Deliberately raw sqlite3 instead of an ORM — the spec asks for 2 simple
tables, and an ORM would be over-engineering for that. Each function opens
its own short-lived connection, which is fine at SQLite's scale and keeps
things simple to reason about.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "crm.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call on every startup."""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            priority TEXT NOT NULL DEFAULT 'Medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id),
            note_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
        CREATE INDEX IF NOT EXISTS idx_notes_ticket_id ON notes(ticket_id);
        """
    )

    # Migration for a DB created before priority existed — CREATE TABLE
    # IF NOT EXISTS above won't retroactively add the column.
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(tickets)")}
    if "priority" not in existing_columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium'")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority)")

    conn.commit()
    conn.close()