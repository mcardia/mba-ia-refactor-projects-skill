"""Index, health check and admin endpoints."""
import logging

from flask import current_app, jsonify

from config.constants import VERSAO_API
from controllers.validators import corpo_json
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
        "ambiente": current_app.config["APP_ENV"],
    }), 200


def reset_database():
    sistema_model.resetar_tudo()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    if not current_app.config["ADMIN_SQL_QUERY_ENABLED"]:
        raise ForbiddenError("Endpoint desabilitado")
    query = corpo_json(exigir_conteudo=False).get("sql", "")
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")
    if not query.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    resultado = sistema_model.consultar_somente_leitura(query)
    return jsonify({"dados": resultado, "sucesso": True}), 200
