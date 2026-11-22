"""Produto endpoints: read input, validate, call the model, build the HTTP response."""
import logging

from flask import jsonify, request

from controllers.validators import corpo_json, preco_opcional, validar_produto
from models import produto as produto_model
from utils.errors import NotFoundError

logger = logging.getLogger(__name__)


def _produto_ou_404(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar_produtos():
    produtos = produto_model.listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(produto_id):
    return jsonify({"dados": _produto_ou_404(produto_id), "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = preco_opcional(request.args.get("preco_min"), "preco_min")
    preco_max = preco_opcional(request.args.get("preco_max"), "preco_max")
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    produto = validar_produto(corpo_json())
    novo_id = produto_model.criar(**produto)
    logger.info("Produto criado com ID %s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    _produto_ou_404(produto_id)
    produto = validar_produto(corpo_json())
    produto_model.atualizar(produto_id, **produto)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    _produto_ou_404(produto_id)
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
