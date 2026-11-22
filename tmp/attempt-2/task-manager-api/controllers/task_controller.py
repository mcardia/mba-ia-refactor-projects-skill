import logging

from flask import jsonify, request

from controllers import validators
from database import commit
from models import Task
from services import report_service
from utils.errors import NotFoundError

logger = logging.getLogger(__name__)


def _task_or_404(task_id):
    task = Task.get(task_id)
    if task is None:
        raise NotFoundError(validators.TASK_NOT_FOUND)
    return task


def list_tasks():
    return jsonify([task.to_list_dict() for task in Task.all_with_relations()]), 200


def get_task(task_id):
    return jsonify(_task_or_404(task_id).to_detail_dict()), 200


def create_task():
    fields = validators.task_fields(validators.json_body(), creating=True)
    task = Task(**fields)
    task.add()
    commit('Erro ao criar task')
    logger.info('Task criada: %s', task.id)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = _task_or_404(task_id)
    fields = validators.task_fields(validators.json_body(), creating=False)
    task.apply_changes(fields)
    commit('Erro ao atualizar')
    logger.info('Task atualizada: %s', task.id)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    _task_or_404(task_id).remove()
    commit('Erro ao deletar')
    logger.info('Task deletada: %s', task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = Task.search(
        term=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=validators.int_query_param('priority'),
        user_id=validators.int_query_param('user_id'),
    )
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(report_service.task_stats()), 200
