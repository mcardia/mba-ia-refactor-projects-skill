"""Entry point (composition root): build the app, wire layers, start the server."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database.connection import close_db, init_db
from middlewares.error_handler import register_error_handlers
from views.routes import api

logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)

    if app.config["CORS_ORIGINS"]:
        CORS(app, origins=app.config["CORS_ORIGINS"])

    app.teardown_appcontext(close_db)
    register_error_handlers(app)
    app.register_blueprint(api)
    init_db(app.config["DATABASE_PATH"])
    return app


app = create_app()


if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", app.config["HOST"], app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
