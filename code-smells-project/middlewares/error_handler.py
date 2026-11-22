"""Centralized error handling: one JSON envelope {"erro": ..., "sucesso": False}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.mensagem, "sucesso": False}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err  # 404/405 for unknown routes keep Flask's default response
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
