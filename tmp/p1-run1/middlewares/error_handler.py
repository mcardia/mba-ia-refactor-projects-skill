"""Centralized error handling: one JSON envelope {"erro": ..., "sucesso": False}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


def resposta_erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return resposta_erro(err.mensagem, err.status)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):  # 404/405 etc. keep Flask's default response
            return err
        logger.exception("Erro não tratado")
        return resposta_erro(MENSAGEM_ERRO_INTERNO, 500)
