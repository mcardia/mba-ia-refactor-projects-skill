"""Usuario: persistence, serialization (never exposes the password) and authentication."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import TIPO_USUARIO_PADRAO
from database.connection import get_db

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def _to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def _to_login_dict(row):
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def criar(nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
    conn = get_db()
    with conn:
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def _senha_confere(armazenada, candidata):
    armazenada = armazenada or ""
    if armazenada.startswith(_PREFIXOS_HASH):
        return check_password_hash(armazenada, candidata), False
    # Legacy plaintext value from a database created before hashing: verify once, then re-hash.
    return hmac.compare_digest(armazenada.encode(), candidata.encode()), True


def autenticar(email, senha):
    """Return the public user dict when the credentials match, otherwise None."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
    for row in rows:
        confere, legado = _senha_confere(row["senha"], senha)
        if confere:
            if legado:
                with conn:
                    conn.execute(
                        "UPDATE usuarios SET senha = ? WHERE id = ?",
                        (generate_password_hash(senha), row["id"]),
                    )
            return _to_login_dict(row)
    return None
