"""Category use cases."""
from config.constants import DEFAULT_COLOR
from controllers import validators
from database import commit
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError, ValidationError


def _get_category_or_404(category_id):
    category = Category.find(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    counts = Task.count_by_category()
    return [(category, counts.get(category.id, 0)) for category in Category.list_all()]


def create_category(data):
    data = validators.require_json_object(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    category = Category(
        name=validators.required_name(name),
        description=validators.optional_text(data.get('description', ''), 'Descrição'),
        color=validators.color(data.get('color', DEFAULT_COLOR)),
    )
    category.add()
    commit('Erro ao criar categoria')
    return category


def update_category(category_id, data):
    category = _get_category_or_404(category_id)
    data = validators.require_json_object(data)
    if 'name' in data:
        category.name = validators.required_name(data['name'])
    if 'description' in data:
        category.description = validators.optional_text(data['description'], 'Descrição')
    if 'color' in data:
        category.color = validators.color(data['color'])
    commit('Erro ao atualizar')
    return category


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    category.remove()   # tasks of this category are detached (category_id = NULL)
    commit('Erro ao deletar')
