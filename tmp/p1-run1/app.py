"""Entry point / composition root. Run with: python app.py"""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import load_settings
from database.connection import close_db
from database.schema import init_db
from middlewares.error_handler import register_error_handlers
from views.routes import api

logger = logging.getLogger(__name__)


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_settings())
    if overrides:
        app.config.update(overrides)

    logging.basicConfig(level=app.config["LOG_LEVEL"],
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    CORS(app, origins=app.config["CORS_ORIGINS"])
    init_db(app.config["DATABASE_PATH"])
    app.teardown_appcontext(close_db)
    register_error_handlers(app)
    app.register_blueprint(api)
    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", app.config["HOST"], app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
