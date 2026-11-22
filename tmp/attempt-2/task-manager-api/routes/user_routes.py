from flask import Blueprint

from controllers import user_controller as users
from middlewares.auth import require_admin

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/users', view_func=users.list_users, methods=['GET'])
user_bp.add_url_rule('/users', view_func=users.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=users.get_user, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=users.update_user, methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_admin(users.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=users.list_user_tasks, methods=['GET'])
user_bp.add_url_rule('/login', view_func=users.login, methods=['POST'])
