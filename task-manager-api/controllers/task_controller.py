import logging

from flask import jsonify, request

from controllers import validators
from models.task import Task
from routes import serializers
from services import report_service
from utils.errors import NotFoundError
from utils.time import utc_now

logger = logging.getLogger(__name__)


def _task_or_404(task_id):
    task = Task.get_by_id(task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def list_tasks():
    now = utc_now()
    return jsonify([serializers.task_list_item(task, now) for task in Task.list_with_relations()]), 200


def get_task(task_id):
    return jsonify(serializers.task_with_overdue(_task_or_404(task_id))), 200


def create_task():
    fields = validators.task_fields_for_create(validators.json_body())
    task = Task.create(**fields)
    logger.info('Task criada: %s', task.id)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = _task_or_404(task_id)
    fields = validators.task_fields_for_update(validators.json_body())
    task.update(fields)
    logger.info('Task atualizada: %s', task.id)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = _task_or_404(task_id)
    task.delete()
    logger.info('Task deletada: %s', task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    tasks = Task.search(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=validators.int_query_param('priority'),
        user_id=validators.int_query_param('user_id'),
    )
    return jsonify([task.to_dict() for task in tasks]), 200


def task_stats():
    return jsonify(report_service.task_stats()), 200
