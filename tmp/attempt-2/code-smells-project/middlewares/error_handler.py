"""Centralized error handling: one JSON envelope {"erro": ..., "sucesso": false}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)


def resposta_erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(erro):
        return resposta_erro(erro.mensagem, erro.status)

    @app.errorhandler(Exception)
    def handle_unexpected(erro):
        if isinstance(erro, HTTPException):  # 404/405 for unknown routes keep Flask's default
            return erro
        logger.exception("Erro não tratado")
        return resposta_erro("Erro interno do servidor", 500)
