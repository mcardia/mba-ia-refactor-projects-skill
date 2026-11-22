"""Produto: persistence and entity rules."""
from config.constants import CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from database.connection import get_db
from utils.errors import ConflictError, ValidationError

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def para_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


def validar(nome, preco, estoque, categoria):
    """Entity invariants, shared by create and update."""
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))


def listar():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [para_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return para_dict(row) if row else None


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
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clausulas)
    return [para_dict(row) for row in get_db().execute(sql, parametros).fetchall()]


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
    """Refuses to delete a product referenced by orders (would orphan itens_pedido)."""
    conn = get_db()
    with conn:
        vinculado = conn.execute(
            "SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)
        ).fetchone()
        if vinculado:
            raise ConflictError("Produto possui pedidos vinculados e não pode ser deletado")
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
