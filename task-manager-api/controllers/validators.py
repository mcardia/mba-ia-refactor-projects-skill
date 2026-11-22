"""Input validation shared by the controllers. Every failure raises a domain error."""
import re
from datetime import datetime

from config.constants import (COLOR_PATTERN, DATE_FORMAT, EMAIL_PATTERN, PRIORITY_MAX,
                              PRIORITY_MIN, TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH,
                              USER_ROLES)
from utils.errors import ValidationError


def require_json_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def task_title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def task_status(value):
    if value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def task_priority(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError('Prioridade inválida')
    if value < PRIORITY_MIN or value > PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return value


def due_date(value, error_message):
    if not isinstance(value, str):
        raise ValidationError(error_message)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError(error_message)


def tags(value):
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return value
    if isinstance(value, str):
        return value
    raise ValidationError('Tags inválidas')


def optional_text(value, field_label):
    if value is not None and not isinstance(value, str):
        raise ValidationError(f'{field_label} inválida')
    return value


def query_int(value, error_message):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(error_message)


def required_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError('Nome é obrigatório')
    return value


def email(value):
    if not isinstance(value, str) or not re.match(EMAIL_PATTERN, value):
        raise ValidationError('Email inválido')
    return value


def password(value, min_length, too_short_message):
    if not isinstance(value, str):
        raise ValidationError('Senha inválida')
    if len(value) < min_length:
        raise ValidationError(too_short_message)
    return value


def role(value):
    if value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def boolean(value, field_label):
    if not isinstance(value, bool):
        raise ValidationError(f'Campo {field_label} inválido')
    return value


def color(value):
    if not isinstance(value, str) or not re.match(COLOR_PATTERN, value):
        raise ValidationError('Cor inválida')
    return value
