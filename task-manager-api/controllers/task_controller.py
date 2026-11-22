"""Task use cases: validate input, call the models, raise domain errors."""
import logging

from config.constants import DEFAULT_PRIORITY, STATUS_PENDING
from controllers import validators
from database import commit
from models.category import Category
from models.task import Task
from models.user import User
from utils.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = Task.find(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_user_exists(user_id):
    if user_id and not User.find(user_id):
        raise NotFoundError('Usuário não encontrado')


def _ensure_category_exists(category_id):
    if category_id and not Category.find(category_id):
        raise NotFoundError('Categoria não encontrada')


def list_tasks():
    return Task.list_with_relations()


def get_task(task_id):
    return _get_task_or_404(task_id)


def create_task(data):
    data = validators.require_json_object(data)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    title = validators.task_title(title)

    description = validators.optional_text(data.get('description', ''), 'Descrição')
    status = validators.task_status(data.get('status', STATUS_PENDING))
    priority = validators.task_priority(data.get('priority', DEFAULT_PRIORITY))
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    _ensure_user_exists(user_id)
    _ensure_category_exists(category_id)

    task = Task(title=title, description=description, status=status, priority=priority,
                user_id=user_id, category_id=category_id)
    if data.get('due_date'):
        task.due_date = validators.due_date(data['due_date'],
                                            'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        task.tags = Task.tags_to_column(validators.tags(data['tags']))

    task.add()
    commit('Erro ao criar task')
    logger.info('Task criada: %s', task.id)
    return task


def update_task(task_id, data):
    task = _get_task_or_404(task_id)
    data = validators.require_json_object(data)

    if 'title' in data:
        task.title = validators.task_title(data['title'])
    if 'description' in data:
        task.description = validators.optional_text(data['description'], 'Descrição')
    if 'status' in data:
        task.status = validators.task_status(data['status'])
    if 'priority' in data:
        task.priority = validators.task_priority(data['priority'])
    if 'user_id' in data:
        _ensure_user_exists(data['user_id'])
        task.user_id = data['user_id']
    if 'category_id' in data:
        _ensure_category_exists(data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        task.due_date = (validators.due_date(data['due_date'], 'Formato de data inválido')
                         if data['due_date'] else None)
    if 'tags' in data:
        task.tags = (None if data['tags'] is None
                     else Task.tags_to_column(validators.tags(data['tags'])))

    task.touch()
    commit('Erro ao atualizar')
    logger.info('Task atualizada: %s', task.id)
    return task


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    task.remove()
    commit('Erro ao deletar')
    logger.info('Task deletada: %s', task_id)


def search_tasks(args):
    return Task.search(
        text=args.get('q', ''),
        status=args.get('status', ''),
        priority=validators.query_int(args.get('priority'), 'Prioridade inválida'),
        user_id=validators.query_int(args.get('user_id'), 'Usuário inválido'),
    )
