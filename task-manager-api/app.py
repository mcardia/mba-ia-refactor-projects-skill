"""Entry point / composition root. Run with: python app.py"""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_routes

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)
    if not settings.SECRET_KEY_FROM_ENV:
        logger.warning('SECRET_KEY not set: using a random key; login tokens expire on restart')

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    db.init_app(app)
    register_error_handlers(app)
    register_routes(app)

    with app.app_context():
        import models  # noqa: F401  (registers every model before create_all)
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
