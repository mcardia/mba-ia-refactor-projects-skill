from flask import jsonify

from config.constants import DEFAULT_COLOR
from controllers import validators
from models.category import Category
from models.task import Task
from routes import serializers
from utils.errors import NotFoundError


def _category_or_404(category_id):
    category = Category.get_by_id(category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    task_counts = Task.count_by_category()
    return jsonify([serializers.category_list_item(category, task_counts.get(category.id, 0))
                    for category in Category.list_all()]), 200


def create_category():
    data = validators.json_body()
    category = Category.create(
        name=validators.category_name(data.get('name'), required=True),
        description=validators.category_description(data.get('description', '')),
        color=validators.color(data.get('color', DEFAULT_COLOR)),
    )
    return jsonify(category.to_dict()), 201


def update_category(category_id):
    category = _category_or_404(category_id)
    data = validators.json_body()
    fields = {}
    if 'name' in data:
        fields['name'] = validators.category_name(data['name'], required=True)
    if 'description' in data:
        fields['description'] = validators.category_description(data['description'])
    if 'color' in data:
        fields['color'] = validators.color(data['color'])
    category.update(fields)
    return jsonify(category.to_dict()), 200


def delete_category(category_id):
    _category_or_404(category_id).delete_detaching_tasks()
    return jsonify({'message': 'Categoria deletada'}), 200
