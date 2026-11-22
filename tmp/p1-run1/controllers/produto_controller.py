"""HTTP flow for /produtos."""
import logging

from flask import jsonify, request

from config.constants import CATEGORIA_PADRAO
from controllers import validators
from models import produto as produto_model
from utils.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _dados_produto():
    dados = validators.corpo_json()
    for campo, mensagem in (("nome", "Nome é obrigatório"),
                            ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)
    campos = {
        "nome": validators.texto(dados["nome"], "Nome deve ser texto"),
        "descricao": validators.texto(dados.get("descricao", ""), "Descrição deve ser texto"),
        "preco": validators.numero(dados["preco"], "Preço deve ser numérico"),
        "estoque": validators.numero(dados["estoque"], "Estoque deve ser numérico"),
        "categoria": dados.get("categoria", CATEGORIA_PADRAO),
    }
    produto_model.validar(campos["nome"], campos["preco"], campos["estoque"], campos["categoria"])
    return campos


def _produto_existente(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def listar_produtos():
    produtos = produto_model.listar()
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(produto_id):
    return jsonify({"dados": _produto_existente(produto_id), "sucesso": True}), 200


def buscar_produtos():
    resultados = produto_model.buscar(
        request.args.get("q", ""),
        request.args.get("categoria", None),
        validators.numero_query("preco_min"),
        validators.numero_query("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    campos = _dados_produto()
    produto_id = produto_model.criar(**campos)
    logger.info("Produto criado com ID %s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(produto_id):
    _produto_existente(produto_id)
    campos = _dados_produto()
    produto_model.atualizar(produto_id, **campos)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id):
    _produto_existente(produto_id)
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
