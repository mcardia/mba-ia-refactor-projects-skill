import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):  # unknown route, wrong method...: framework default
            return err
        logger.exception('Unhandled error')
        return jsonify({'error': GENERIC_ERROR_MESSAGE}), 500
