"""Produto: persistence and row mapping."""
from database.connection import get_db
from utils.errors import ConflictError

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def produto_to_dict(row):
    return {campo: row[campo] for campo in _CAMPOS}


def listar():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [produto_to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return produto_to_dict(row) if row else None


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    clauses, params = ["1=1"], []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)
    rows = get_db().execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params).fetchall()
    return [produto_to_dict(row) for row in rows]


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
    """Delete a product that no order item references (keeps order history consistent)."""
    conn = get_db()
    with conn:
        vinculado = conn.execute(
            "SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)
        ).fetchone()
        if vinculado:
            raise ConflictError("Produto possui pedidos vinculados e não pode ser deletado")
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
