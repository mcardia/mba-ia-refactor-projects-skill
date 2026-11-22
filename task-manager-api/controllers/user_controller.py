"""User and authentication use cases."""
import logging

from flask import current_app
from itsdangerous import URLSafeTimedSerializer

from config.constants import MIN_PASSWORD_LENGTH, ROLE_USER, TOKEN_SALT
from controllers import validators
from database import commit
from middlewares.auth import ensure_admin
from models.task import Task
from models.user import User
from utils.errors import (ConflictError, ForbiddenError, NotFoundError, UnauthorizedError,
                          ValidationError)

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = User.find(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_users():
    """Users with their task count (one aggregate query instead of one per user)."""
    counts = Task.count_by_user()
    return [(user, counts.get(user.id, 0)) for user in User.list_all()]


def get_user(user_id):
    user = _get_user_or_404(user_id)
    return user, Task.list_by_user(user_id)


def create_user(data):
    data = validators.require_json_object(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    role = data.get('role', ROLE_USER)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validators.required_name(name)
    validators.email(email)
    validators.password(password, MIN_PASSWORD_LENGTH, 'Senha deve ter no mínimo 4 caracteres')
    if User.find_by_email(email):
        raise ConflictError('Email já cadastrado')
    validators.role(role)
    if role != ROLE_USER:
        ensure_admin()   # only an administrator may create privileged accounts

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    user.add()
    commit('Erro ao criar usuário')
    logger.info('Usuário criado: %s', user.id)
    return user


def update_user(user_id, data):
    user = _get_user_or_404(user_id)
    data = validators.require_json_object(data)

    if 'name' in data:
        user.name = validators.required_name(data['name'])
    if 'email' in data:
        validators.email(data['email'])
        existing = User.find_by_email(data['email'])
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = data['email']
    if 'password' in data:
        user.set_password(validators.password(data['password'], MIN_PASSWORD_LENGTH,
                                              'Senha muito curta'))
    if 'role' in data:
        validators.role(data['role'])
        ensure_admin()   # role changes are privileged
        user.role = data['role']
    if 'active' in data:
        user.active = validators.boolean(data['active'], 'active')

    commit('Erro ao atualizar')
    return user


def delete_user(user_id):
    user = _get_user_or_404(user_id)
    user.delete_with_tasks()
    commit('Erro ao deletar')
    logger.info('Usuário deletado: %s', user_id)


def get_user_tasks(user_id):
    _get_user_or_404(user_id)
    return Task.list_by_user(user_id)


def login(data):
    data = validators.require_json_object(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email)
    if not user or not isinstance(password, str) or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    if user.has_unsaved_changes():
        commit('Erro ao autenticar')   # persists a legacy hash upgraded during check_password

    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)
    return user, serializer.dumps({'uid': user.id})
