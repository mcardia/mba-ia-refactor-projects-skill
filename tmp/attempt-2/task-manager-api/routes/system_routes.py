from flask import Blueprint

from controllers import system_controller as system

system_bp = Blueprint('system', __name__)

system_bp.add_url_rule('/health', view_func=system.health, methods=['GET'])
system_bp.add_url_rule('/', view_func=system.index, methods=['GET'])
