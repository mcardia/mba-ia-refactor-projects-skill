"""Route registration: URL + HTTP method -> controller."""
from flask import Blueprint

from controllers import (
    pedido_controller as pedidos,
    produto_controller as produtos,
    relatorio_controller as relatorios,
    sistema_controller as sistema,
    usuario_controller as usuarios,
)
from middlewares.auth import require_admin

api = Blueprint("api", __name__)

api.add_url_rule("/produtos", "listar_produtos", produtos.listar_produtos, methods=["GET"])
api.add_url_rule("/produtos/busca", "buscar_produtos", produtos.buscar_produtos, methods=["GET"])
api.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produtos.buscar_produto, methods=["GET"])
api.add_url_rule("/produtos", "criar_produto", produtos.criar_produto, methods=["POST"])
api.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produtos.atualizar_produto, methods=["PUT"])
api.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produtos.deletar_produto, methods=["DELETE"])

api.add_url_rule("/usuarios", "listar_usuarios", usuarios.listar_usuarios, methods=["GET"])
api.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuarios.buscar_usuario, methods=["GET"])
api.add_url_rule("/usuarios", "criar_usuario", usuarios.criar_usuario, methods=["POST"])
api.add_url_rule("/login", "login", usuarios.login, methods=["POST"])

api.add_url_rule("/pedidos", "criar_pedido", pedidos.criar_pedido, methods=["POST"])
api.add_url_rule("/pedidos", "listar_todos_pedidos", pedidos.listar_todos_pedidos, methods=["GET"])
api.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                 pedidos.listar_pedidos_usuario, methods=["GET"])
api.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                 pedidos.atualizar_status_pedido, methods=["PUT"])

api.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorios.relatorio_vendas, methods=["GET"])

api.add_url_rule("/health", "health_check", sistema.health_check, methods=["GET"])
api.add_url_rule("/", "index", sistema.index, methods=["GET"])

api.add_url_rule("/admin/reset-db", "reset_database", require_admin(sistema.reset_database), methods=["POST"])
api.add_url_rule("/admin/query", "executar_query", require_admin(sistema.executar_query), methods=["POST"])
