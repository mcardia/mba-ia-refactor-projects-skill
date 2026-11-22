"""Input validation shared by create and update flows. Every failure raises a domain error."""
import re
from datetime import datetime

from flask import request

from config.constants import (COLOR_PATTERN, DEFAULT_PRIORITY, DUE_DATE_FORMAT, EMAIL_PATTERN, PASSWORD_MIN_LENGTH,
                              PRIORITY_MAX, PRIORITY_MIN, STATUS_PENDING, TASK_STATUSES, TITLE_MAX_LENGTH,
                              TITLE_MIN_LENGTH, USER_ROLES)
from models import Category, User
from utils.errors import NotFoundError, ValidationError

INVALID_BODY = 'Dados inválidos'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'
TASK_NOT_FOUND = 'Task não encontrada'
NAME_REQUIRED = 'Nome é obrigatório'


def json_body():
    """The request JSON object; a missing, malformed or non-object body is a 400."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        raise ValidationError(INVALID_BODY)
    return data


def int_query_param(name):
    raw = request.args.get(name, '')
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido') from None


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# ---- tasks ------------------------------------------------------------------------------------
def _title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _status(value):
    if not isinstance(value, str) or value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    if not is_int(value) or not PRIORITY_MIN <= value <= PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return value


def _reference(model, value, not_found_message):
    if not value:
        return None
    if not is_int(value) or model.get(value) is None:
        raise NotFoundError(not_found_message)
    return value


def _due_date(value, error_message):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError(error_message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(error_message) from None


def _tags(value):
    if not value:
        return None
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return ','.join(value)
    if isinstance(value, str):
        return value
    raise ValidationError('Tags inválidas')


def task_fields(data, creating):
    """Validated column values for a task. On create, applies the defaults and requires a title."""
    if creating:
        if not data.get('title'):
            raise ValidationError('Título é obrigatório')
        data = {'description': '', 'status': STATUS_PENDING, 'priority': DEFAULT_PRIORITY, **data}
    date_error = 'Formato de data inválido. Use YYYY-MM-DD' if creating else 'Formato de data inválido'

    fields = {}
    if 'title' in data:
        fields['title'] = _title(data['title'])
    if 'description' in data:
        fields['description'] = data['description']
    if 'status' in data:
        fields['status'] = _status(data['status'])
    if 'priority' in data:
        fields['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _reference(User, data['user_id'], USER_NOT_FOUND)
    if 'category_id' in data:
        fields['category_id'] = _reference(Category, data['category_id'], CATEGORY_NOT_FOUND)
    if 'due_date' in data:
        fields['due_date'] = _due_date(data['due_date'], date_error)
    if 'tags' in data:
        fields['tags'] = _tags(data['tags'])
    return fields


# ---- users ------------------------------------------------------------------------------------
def name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(NAME_REQUIRED)
    return value


def email(value):
    if not isinstance(value, str) or not re.match(EMAIL_PATTERN, value):
        raise ValidationError('Email inválido')
    return value


def password(value, too_short_message):
    if not isinstance(value, str) or len(value) < PASSWORD_MIN_LENGTH:
        raise ValidationError(too_short_message)
    return value


def role(value):
    if not isinstance(value, str) or value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def active_flag(value):
    if not isinstance(value, bool):
        raise ValidationError('Campo active inválido')
    return value


# ---- categories -------------------------------------------------------------------------------
def color(value):
    if not isinstance(value, str) or not re.match(COLOR_PATTERN, value):
        raise ValidationError('Cor inválida')
    return value
