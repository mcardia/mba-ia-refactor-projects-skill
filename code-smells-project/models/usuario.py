"""Usuario: persistence, row mapping (never exposes the password) and credential check."""
from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import TIPO_USUARIO_PADRAO
from database.connection import get_db

_CAMPOS = ("id", "nome", "email", "tipo", "criado_em")
_CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def usuario_to_dict(row, campos=_CAMPOS):
    return {campo: row[campo] for campo in campos}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [usuario_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return usuario_to_dict(row) if row else None


def existe(usuario_id):
    return get_db().execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def autenticar(email, senha):
    rows = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall()
    for row in rows:
        if row["senha"] and check_password_hash(row["senha"], senha):
            return usuario_to_dict(row, _CAMPOS_LOGIN)
    return None


def criar(nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
    conn = get_db()
    with conn:
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid
