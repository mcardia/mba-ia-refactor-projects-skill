"""Single place that turns exceptions into the API's JSON error envelope {'error': message}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from utils.errors import AppError

logger = logging.getLogger(__name__)

_HTTP_MESSAGES = {
    400: 'Dados inválidos',
    404: 'Recurso não encontrado',
    405: 'Método não permitido',
    415: 'Dados inválidos',
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        if err.status >= 500:
            db.session.rollback()
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({'error': _HTTP_MESSAGES.get(err.code, err.name)}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        logger.exception('Unhandled error')
        return jsonify({'error': 'Erro interno'}), 500
