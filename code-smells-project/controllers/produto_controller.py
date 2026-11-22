"""Produto endpoints: read input, validate, call the model, build the response."""
import logging

from flask import jsonify, request

from controllers import validators
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
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(produto_id):
    return jsonify({"dados": _produto_ou_404(produto_id), "sucesso": True}), 200


def buscar_produtos():
    resultados = produto_model.buscar(
        request.args.get("q", ""),
        request.args.get("categoria") or None,
        validators.parametro_numerico("preco_min"),
        validators.parametro_numerico("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    produto = validators.validar_produto(validators.corpo_json())
    produto_id = produto_model.criar(**produto)
    logger.info("Produto criado com ID: %s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    _produto_ou_404(produto_id)
    produto = validators.validar_produto(validators.corpo_json())
    produto_model.atualizar(produto_id, **produto)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    _produto_ou_404(produto_id)
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
