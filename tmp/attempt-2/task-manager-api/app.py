import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_routes
from services.auth_service import TokenService


def create_app(settings=Settings):
    """Composition root: config, database, services, error handling and routes."""
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    db.init_app(app)
    app.extensions['token_service'] = TokenService(settings.SECRET_KEY, settings.TOKEN_MAX_AGE_SECONDS)

    register_error_handlers(app)
    register_routes(app)

    with app.app_context():
        import models  # noqa: F401  (registers the tables)
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
