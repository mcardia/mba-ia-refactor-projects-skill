"""URL + method -> controller mapping. No logic here."""
from flask import Blueprint

from controllers import (admin_controller, pedido_controller, produto_controller,
                         relatorio_controller, sistema_controller, usuario_controller)
from middlewares.auth import require_admin

api = Blueprint("api", __name__)

ROTAS = [
    ("/produtos", produto_controller.listar_produtos, ["GET"]),
    ("/produtos/busca", produto_controller.buscar_produtos, ["GET"]),
    ("/produtos/<int:produto_id>", produto_controller.buscar_produto, ["GET"]),
    ("/produtos", produto_controller.criar_produto, ["POST"]),
    ("/produtos/<int:produto_id>", produto_controller.atualizar_produto, ["PUT"]),
    ("/produtos/<int:produto_id>", produto_controller.deletar_produto, ["DELETE"]),

    ("/usuarios", usuario_controller.listar_usuarios, ["GET"]),
    ("/usuarios/<int:usuario_id>", usuario_controller.buscar_usuario, ["GET"]),
    ("/usuarios", usuario_controller.criar_usuario, ["POST"]),
    ("/login", usuario_controller.login, ["POST"]),

    ("/pedidos", pedido_controller.criar_pedido, ["POST"]),
    ("/pedidos", pedido_controller.listar_todos_pedidos, ["GET"]),
    ("/pedidos/usuario/<int:usuario_id>", pedido_controller.listar_pedidos_usuario, ["GET"]),
    ("/pedidos/<int:pedido_id>/status", pedido_controller.atualizar_status_pedido, ["PUT"]),

    ("/relatorios/vendas", relatorio_controller.relatorio_vendas, ["GET"]),

    ("/health", sistema_controller.health_check, ["GET"]),
    ("/", sistema_controller.index, ["GET"]),

    ("/admin/reset-db", require_admin(admin_controller.reset_database), ["POST"]),
    ("/admin/query", require_admin(admin_controller.executar_query), ["POST"]),
]

for caminho, controller, metodos in ROTAS:
    api.add_url_rule(caminho, view_func=controller, methods=metodos)
