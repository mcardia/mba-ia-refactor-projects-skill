"""Centralized error handling: every domain error becomes {'error': <message>}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        db.session.rollback()
        logger.exception('Unhandled error')
        return jsonify({'error': 'Erro interno'}), 500
