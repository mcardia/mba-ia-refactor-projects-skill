"""Request-scoped SQLite connections. The database path comes from the app config."""
import sqlite3
from pathlib import Path

from flask import current_app, g


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """One connection per request, closed by close_db at teardown."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def connect_read_only():
    """Separate connection that SQLite itself prevents from writing."""
    uri = Path(current_app.config["DATABASE_PATH"]).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
