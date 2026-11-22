"""Whole-database operations: health counts, reset, read-only SQL console."""
import sqlite3

from database.connection import connect_read_only, get_db
from utils.errors import ValidationError


def contar_entidades():
    row = get_db().execute(
        "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
        "(SELECT COUNT(*) FROM usuarios) AS usuarios, "
        "(SELECT COUNT(*) FROM pedidos) AS pedidos"
    ).fetchone()
    return dict(row)


def resetar_banco():
    conn = get_db()
    with conn:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):  # children first
            conn.execute(f"DELETE FROM {tabela}")  # fixed whitelist, no user input


def consultar_somente_leitura(sql):
    """Runs a single SELECT on a read-only connection."""
    if not sql.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    conn = connect_read_only()
    try:
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error:
        raise ValidationError("Consulta inválida")
    finally:
        conn.close()
    return [dict(row) for row in rows]
