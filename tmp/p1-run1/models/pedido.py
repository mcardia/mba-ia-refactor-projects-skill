"""Pedido and itens_pedido: persistence, atomic order creation and sales aggregates."""
from config.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from database.connection import get_db
from utils.errors import ValidationError

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT o.id, o.usuario_id, o.status, o.total, o.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           CASE WHEN p.id IS NULL THEN 'Desconhecido' ELSE p.nome END AS produto_nome,
           i.id AS item_id
    FROM pedidos o
    LEFT JOIN itens_pedido i ON i.pedido_id = o.id
    LEFT JOIN produtos p ON p.id = i.produto_id
"""


def _agrupar(rows):
    pedidos = {}
    for row in rows:
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
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar(usuario_id=None):
    """All orders with their items in a single query (optionally filtered by user)."""
    sql, parametros = _SELECT_PEDIDOS_COM_ITENS, []
    if usuario_id is not None:
        sql += " WHERE o.usuario_id = ?"
        parametros.append(usuario_id)
    sql += " ORDER BY o.id, i.id"
    return _agrupar(get_db().execute(sql, parametros).fetchall())


def existe(pedido_id):
    return get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def criar(usuario_id, itens):
    """Validates stock and writes order, items and stock decrements in one transaction.

    `itens` is a list of {"produto_id": int, "quantidade": int > 0}.
    Raises ValidationError (and rolls back) on a missing product or insufficient stock.
    """
    conn = get_db()
    ids = sorted({item["produto_id"] for item in itens})
    marcadores = ", ".join("?" for _ in ids)
    produtos = {
        row["id"]: row
        for row in conn.execute(
            f"SELECT id, nome, preco, estoque FROM produtos WHERE id IN ({marcadores})", ids
        ).fetchall()
    }

    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError("Estoque insuficiente para " + produto["nome"])
        total = total + (produto["preco"] * item["quantidade"])

    with conn:  # commit on success, rollback on any exception
        pedido_id = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid
        for item in itens:
            produto = produtos[item["produto_id"]]
            baixa = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if baixa.rowcount == 0:  # concurrent sale or repeated item exhausted the stock
                raise ValidationError("Estoque insuficiente para " + produto["nome"])
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    conn = get_db()
    with conn:
        conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def totais_vendas():
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
