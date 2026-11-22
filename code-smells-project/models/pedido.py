"""Pedido / itens_pedido: atomic creation, listing (single JOIN) and sales aggregates."""
from config.constants import PRODUTO_DESCONHECIDO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from database.connection import get_db
from utils.errors import ValidationError

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.id AS produto_existente, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def criar(usuario_id, itens):
    """Create the order, its items and the stock decrements in one transaction."""
    conn = get_db()
    with conn:  # commit on success, rollback on any exception
        total = 0
        nomes = {}
        for item in itens:
            produto = conn.execute(
                "SELECT nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"])
            nomes[item["produto_id"]] = produto["nome"]
            total = total + (produto["preco"] * item["quantidade"])

        pedido_id = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid

        for item in itens:
            baixa = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if baixa.rowcount == 0:
                raise ValidationError("Estoque insuficiente para " + nomes[item["produto_id"]])
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "SELECT ?, id, ?, preco FROM produtos WHERE id = ?",
                (pedido_id, item["quantidade"], item["produto_id"]),
            )
    return {"pedido_id": pedido_id, "total": total}


def _agrupar(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["id"])
        if pedido is None:
            pedido = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["id"]] = pedido
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] if row["produto_existente"] is not None else PRODUTO_DESCONHECIDO,
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar_todos():
    rows = get_db().execute(_SELECT_PEDIDOS_COM_ITENS + " ORDER BY p.id, i.id").fetchall()
    return _agrupar(rows)


def listar_por_usuario(usuario_id):
    rows = get_db().execute(
        _SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
    ).fetchall()
    return _agrupar(rows)


def atualizar_status(pedido_id, novo_status):
    """Return True when the order exists and was updated."""
    conn = get_db()
    with conn:
        cursor = conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    return cursor.rowcount > 0


def resumo_vendas():
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(row)
