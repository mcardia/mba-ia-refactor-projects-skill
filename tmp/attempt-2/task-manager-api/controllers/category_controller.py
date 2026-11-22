from flask import jsonify

from config.constants import DEFAULT_CATEGORY_COLOR
from controllers import validators
from database import commit
from models import Category, Task
from utils.errors import NotFoundError, ValidationError


def _category_or_404(category_id):
    category = Category.get(category_id)
    if category is None:
        raise NotFoundError(validators.CATEGORY_NOT_FOUND)
    return category


def list_categories():
    task_counts = Task.count_by_category()
    result = []
    for category in Category.all():
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return jsonify(result), 200


def create_category():
    data = validators.json_body()
    if not data.get('name'):
        raise ValidationError(validators.NAME_REQUIRED)
    category = Category(
        name=validators.name(data['name']),
        description=data.get('description', ''),
        color=validators.color(data.get('color', DEFAULT_CATEGORY_COLOR)),
    )
    category.add()
    commit('Erro ao criar categoria')
    return jsonify(category.to_dict()), 201


def update_category(category_id):
    category = _category_or_404(category_id)
    data = validators.json_body()
    if 'name' in data:
        category.name = validators.name(data['name'])
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = validators.color(data['color'])
    commit('Erro ao atualizar')
    return jsonify(category.to_dict()), 200


def delete_category(category_id):
    _category_or_404(category_id).remove()
    commit('Erro ao deletar')
    return jsonify({'message': 'Categoria deletada'}), 200
