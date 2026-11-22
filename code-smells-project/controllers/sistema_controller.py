"""Index, health check and admin endpoints."""
import logging

from flask import current_app, jsonify

from config.constants import VERSAO_API
from controllers import validators
from models import sistema as sistema_model
from utils.errors import ForbiddenError, ValidationError

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSAO_API,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contagens(),
        "versao": VERSAO_API,
        "ambiente": current_app.config["AMBIENTE"],
    }), 200


def reset_database():
    sistema_model.resetar_banco()
    logger.warning("Banco de dados resetado pelo endpoint administrativo")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    if not current_app.config["ALLOW_ADMIN_QUERY"]:
        raise ForbiddenError("Endpoint desabilitado")
    query = validators.corpo_json(obrigatorio=False).get("sql", "")
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")
    return jsonify({"dados": sistema_model.executar_consulta_leitura(query), "sucesso": True}), 200
