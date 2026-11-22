"""Usuario: persistence and credential handling. Password hashes never leave this module."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import TIPO_CLIENTE
from database.connection import get_db

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def para_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


def listar():
    return [para_dict(row) for row in get_db().execute("SELECT * FROM usuarios").fetchall()]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return para_dict(row) if row else None


def existe(usuario_id):
    return get_db().execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def email_cadastrado(email):
    return get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def criar(nome, email, senha, tipo=TIPO_CLIENTE):
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
        return check_password_hash(armazenada, candidata)
    # Legacy rows written before hashing: constant-time compare, re-hashed on success.
    return hmac.compare_digest(armazenada.encode(), candidata.encode())


def autenticar(email, senha):
    conn = get_db()
    for row in conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall():
        if _senha_confere(row["senha"], senha):
            if not (row["senha"] or "").startswith(_PREFIXOS_HASH):
                with conn:
                    conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?",
                                 (generate_password_hash(senha), row["id"]))
            return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None
