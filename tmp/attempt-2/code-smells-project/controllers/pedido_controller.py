"""Pedido endpoints."""
from flask import jsonify

from controllers.validators import corpo_json, validar_pedido
from models import pedido as pedido_model
from services import pedido_service


def criar_pedido():
    usuario_id, itens = validar_pedido(corpo_json())
    resultado = pedido_service.criar_pedido(usuario_id, itens)
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar(usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_model.listar(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = corpo_json(exigir_conteudo=False)
    pedido_service.atualizar_status(pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
