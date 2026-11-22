"""Produto: persistence and serialization."""
from database.connection import get_db
from utils.errors import ConflictError


def _to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row) if row else None


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    clausulas, parametros = ["1=1"], []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        parametros += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        parametros.append(categoria)
    if preco_min:
        clausulas.append("preco >= ?")
        parametros.append(preco_min)
    if preco_max:
        clausulas.append("preco <= ?")
        parametros.append(preco_max)
    rows = get_db().execute(
        "SELECT * FROM produtos WHERE " + " AND ".join(clausulas), parametros
    ).fetchall()
    return [_to_dict(row) for row in rows]


def criar(nome, descricao, preco, estoque, categoria):
    conn = get_db()
    with conn:
        cursor = conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    conn = get_db()
    with conn:
        conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def deletar(produto_id):
    """Delete a product unless order items still reference it (would leave orphans)."""
    conn = get_db()
    with conn:
        vinculado = conn.execute(
            "SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)
        ).fetchone()
        if vinculado:
            raise ConflictError("Produto possui pedidos vinculados e não pode ser deletado")
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
