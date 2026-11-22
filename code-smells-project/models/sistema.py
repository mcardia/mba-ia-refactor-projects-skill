"""System-wide data operations: health counts, database reset, read-only SQL console."""
import sqlite3

from database.connection import get_db, get_readonly_db
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


def resetar_banco():
    conn = get_db()
    with conn:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            conn.execute(f"DELETE FROM {tabela}")  # fixed whitelist of identifiers, no user input


def executar_consulta_leitura(sql):
    """Run one SELECT statement on a read-only connection."""
    comando = sql.strip().rstrip(";").strip()
    if not comando.upper().startswith("SELECT") or ";" in comando:
        raise ValidationError("Apenas uma única consulta SELECT é permitida")
    conn = get_readonly_db()
    try:
        rows = conn.execute(comando).fetchall()
    except sqlite3.Error:
        raise ValidationError("Query inválida")
    finally:
        conn.close()
    return [dict(row) for row in rows]
