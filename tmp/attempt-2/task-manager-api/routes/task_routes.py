from flask import Blueprint

from controllers import task_controller as tasks
from middlewares.auth import require_admin

task_bp = Blueprint('tasks', __name__)

task_bp.add_url_rule('/tasks', view_func=tasks.list_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks', view_func=tasks.create_task, methods=['POST'])
task_bp.add_url_rule('/tasks/search', view_func=tasks.search_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/stats', view_func=tasks.task_stats, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=tasks.get_task, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=tasks.update_task, methods=['PUT'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=require_admin(tasks.delete_task), methods=['DELETE'])
