"""System-level data access: health counts, database reset, read-only admin query."""
import sqlite3
from contextlib import closing

from database.connection import get_db, open_readonly_db
from utils.errors import ValidationError


def contagens():
    row = get_db().execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(row)


def resetar_tudo():
    conn = get_db()
    with conn:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            conn.execute(f"DELETE FROM {tabela}")  # fixed whitelist, no external input


def consultar_somente_leitura(sql):
    """Run one statement on a read-only connection (writes are rejected by SQLite)."""
    with closing(open_readonly_db()) as conn:
        try:
            rows = conn.execute(sql).fetchall()
        except sqlite3.Error as erro:
            raise ValidationError("Query inválida") from erro
    return [dict(row) for row in rows]
