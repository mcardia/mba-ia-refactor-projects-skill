from flask import Blueprint, jsonify, request

from controllers import user_controller
from middlewares.auth import require_admin
from routes import serializers
from utils.time import utc_now

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    users = user_controller.list_users()
    return jsonify([serializers.user_with_task_count(user, count) for user, count in users]), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user, tasks = user_controller.get_user(user_id)
    return jsonify(serializers.user_detail(user, tasks)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user = user_controller.create_user(request.get_json())
    return jsonify(user.to_dict()), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json())
    return jsonify(user.to_dict()), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    tasks = user_controller.get_user_tasks(user_id)
    now = utc_now()
    return jsonify([serializers.user_task_item(task, now) for task in tasks]), 200


@user_bp.route('/login', methods=['POST'])
def login():
    user, token = user_controller.login(request.get_json())
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200
