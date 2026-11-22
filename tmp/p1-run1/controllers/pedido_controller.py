"""HTTP flow for /pedidos."""
from flask import jsonify

from controllers import validators
from models import pedido as pedido_model
from services import pedido_service


def criar_pedido():
    dados = validators.corpo_json()
    resultado = pedido_service.criar_pedido(dados.get("usuario_id"), dados.get("itens", []))
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar(usuario_id=usuario_id), "sucesso": True}), 200


def listar_todos_pedidos():
    return jsonify({"dados": pedido_model.listar(), "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = validators.corpo_json_opcional()
    pedido_service.atualizar_status(pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
