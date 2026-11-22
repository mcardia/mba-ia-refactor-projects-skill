"""HTTP flow for /admin/* (always behind middlewares.auth.require_admin)."""
import logging

from flask import current_app, jsonify

from controllers import validators
from models import sistema as sistema_model
from utils.errors import ForbiddenError, ValidationError

logger = logging.getLogger(__name__)


def reset_database():
    sistema_model.resetar_banco()
    logger.warning("Banco de dados resetado via endpoint administrativo")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    if not current_app.config.get("ADMIN_RAW_QUERY_ENABLED"):
        raise ForbiddenError("Console SQL desabilitado")
    sql = validators.corpo_json_opcional().get("sql", "")
    if not sql or not isinstance(sql, str):
        raise ValidationError("Query não informada")
    return jsonify({"dados": sistema_model.consultar_somente_leitura(sql), "sucesso": True}), 200
