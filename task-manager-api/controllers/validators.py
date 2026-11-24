"""Input validation shared by create and update use cases. Every failure raises a domain error."""
import re
from datetime import datetime

from flask import request

from config.constants import (
    COLOR_PATTERN, DATE_FORMAT, DEFAULT_PRIORITY, EMAIL_PATTERN, PASSWORD_MIN_LENGTH,
    PRIORITY_MAX, PRIORITY_MIN, STATUS_PENDING, TASK_STATUSES, TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH, USER_ROLES,
)
from models.category import Category
from models.user import User
from utils.errors import NotFoundError, ValidationError


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def json_body():
    """The request body as a non-empty JSON object, or 400 'Dados inválidos'."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def int_query_param(name):
    value = request.args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')


# ---- tasks ---------------------------------------------------------------------------------
def _title(value, required):
    if required and not value:
        raise ValidationError('Título é obrigatório')
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _optional_text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


def _status(value):
    if value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    if not _is_int(value):
        raise ValidationError('Prioridade inválida')
    if value < PRIORITY_MIN or value > PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return value


def _reference(value, model, invalid_message, missing_message):
    """Optional foreign key: falsy values pass through; others must be an existing id."""
    if not value:
        return value
    if not _is_int(value):
        raise ValidationError(invalid_message)
    if model.get_by_id(value) is None:
        raise NotFoundError(missing_message)
    return value


def _due_date(value, message):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError(message)


def _tags(value):
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise ValidationError('Tags inválidas')
        return ','.join(value)
    if value is not None and not isinstance(value, str):
        raise ValidationError('Tags inválidas')
    return value


def task_fields_for_create(data):
    fields = {
        'title': _title(data.get('title'), required=True),
        'description': _optional_text(data.get('description', ''), 'Descrição inválida'),
        'status': _status(data.get('status', STATUS_PENDING)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _reference(data.get('user_id'), User, 'Usuário inválido', 'Usuário não encontrado'),
        'category_id': _reference(data.get('category_id'), Category,
                                  'Categoria inválida', 'Categoria não encontrada'),
    }
    if data.get('due_date'):
        fields['due_date'] = _due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        fields['tags'] = _tags(data['tags'])
    return fields


def task_fields_for_update(data):
    fields = {}
    if 'title' in data:
        fields['title'] = _title(data['title'], required=False)
    if 'description' in data:
        fields['description'] = _optional_text(data['description'], 'Descrição inválida')
    if 'status' in data:
        fields['status'] = _status(data['status'])
    if 'priority' in data:
        fields['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _reference(data['user_id'], User, 'Usuário inválido', 'Usuário não encontrado')
    if 'category_id' in data:
        fields['category_id'] = _reference(data['category_id'], Category,
                                           'Categoria inválida', 'Categoria não encontrada')
    if 'due_date' in data:
        fields['due_date'] = _due_date(data['due_date'], 'Formato de data inválido')
    if 'tags' in data:
        fields['tags'] = _tags(data['tags'])
    return fields


# ---- users ---------------------------------------------------------------------------------
def _required_text(value, message):
    if not value or not isinstance(value, str):
        raise ValidationError(message)
    return value


def email(value):
    if not isinstance(value, str) or not re.match(EMAIL_PATTERN, value):
        raise ValidationError('Email inválido')
    return value


def password(value, message):
    if not isinstance(value, str) or len(value) < PASSWORD_MIN_LENGTH:
        raise ValidationError(message)
    return value


def role(value):
    if value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def active_flag(value):
    if not isinstance(value, bool):
        raise ValidationError('Campo active inválido')
    return value


def user_fields_for_create(data):
    """Returns validated fields; email uniqueness is checked by the controller (409)."""
    name = _required_text(data.get('name'), 'Nome é obrigatório')
    email_value = _required_text(data.get('email'), 'Email é obrigatório')
    password_value = _required_text(data.get('password'), 'Senha é obrigatória')
    email(email_value)
    password(password_value, f'Senha deve ter no mínimo {PASSWORD_MIN_LENGTH} caracteres')
    return {'name': name, 'email': email_value, 'password': password_value}


# ---- categories ----------------------------------------------------------------------------
def color(value):
    if not isinstance(value, str) or not re.match(COLOR_PATTERN, value):
        raise ValidationError('Cor inválida')
    return value


def category_name(value, required):
    if required and not value:
        raise ValidationError('Nome é obrigatório')
    return _required_text(value, 'Nome é obrigatório')


def category_description(value):
    return _optional_text(value, 'Descrição inválida')
