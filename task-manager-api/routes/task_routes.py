from flask import Blueprint, jsonify, request

from controllers import report_controller, task_controller
from middlewares.auth import require_admin
from routes import serializers

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(serializers.task_list(task_controller.list_tasks())), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(serializers.task_detail(task_controller.get_task(task_id))), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = task_controller.create_task(request.get_json())
    return jsonify(task.to_dict()), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = task_controller.update_task(task_id, request.get_json())
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@require_admin
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    tasks = task_controller.search_tasks(request.args)
    return jsonify([task.to_dict() for task in tasks]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(report_controller.task_stats()), 200
