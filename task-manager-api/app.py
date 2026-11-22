"""Entry point / composition root: builds the Flask app and starts the server."""
import logging
from datetime import datetime

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  (registers the ORM models before create_all)
from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)

    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    register_error_handlers(app)

    for blueprint in (task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()
    return app


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
app = create_app()

if __name__ == '__main__':
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
