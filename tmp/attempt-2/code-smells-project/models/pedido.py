"""Pedido and itens_pedido: atomic creation, listing with a single JOIN, sales aggregates."""
from config.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from database.connection import get_db
from utils.errors import ValidationError

PRODUTO_DESCONHECIDO = "Desconhecido"


def criar(usuario_id, itens):
    """Create the order, its items and the stock decrements in one transaction."""
    conn = get_db()
    with conn:  # commit on success, rollback on any exception
        total = 0
        produtos = {}
        for item in itens:
            produto = conn.execute(
                "SELECT nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            produtos[item["produto_id"]] = produto
            total = total + (produto["preco"] * item["quantidade"])

        pedido_id = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid

        for item in itens:
            produto = produtos[item["produto_id"]]
            atualizado = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if atualizado.rowcount == 0:  # concurrent sale or repeated item consumed the stock
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
    return {"pedido_id": pedido_id, "total": total}


def listar(usuario_id=None):
    sql = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
               pr.id AS produto_encontrado, pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
    """
    parametros = []
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        parametros.append(usuario_id)
    sql += " ORDER BY p.id, i.id"

    pedidos = {}
    for row in get_db().execute(sql, parametros).fetchall():
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_encontrado"] is not None
                else PRODUTO_DESCONHECIDO,
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def existe(pedido_id):
    return get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def atualizar_status(pedido_id, novo_status):
    conn = get_db()
    with conn:
        conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def resumo_vendas():
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               SUM(total) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(row)
