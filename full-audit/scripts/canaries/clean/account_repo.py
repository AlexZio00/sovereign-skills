"""Account lookups for the reporting service."""
import sqlite3


def find_user_by_email(conn: sqlite3.Connection, email: str):
    cursor = conn.execute("SELECT id, name FROM users WHERE email = ?", (email,))
    return cursor.fetchone()
