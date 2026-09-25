"""User lookups for the reporting service."""


def find_user_by_name(conn, name):
    query = "SELECT id, email FROM users WHERE name = '" + name + "'"
    return conn.execute(query).fetchone()
