import logging

from flask import jsonify

from config.constants import ROLE_ADMIN, ROLE_USER
from controllers import validators
from middlewares.auth import ensure_role, issue_token
from models.task import Task
from models.user import User
from routes import serializers
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from utils.time import utc_now

logger = logging.getLogger(__name__)


def _user_or_404(user_id):
    user = User.get_by_id(user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_users():
    task_counts = Task.count_by_user()
    return jsonify([serializers.user_list_item(user, task_counts.get(user.id, 0))
                    for user in User.list_all()]), 200


def get_user(user_id):
    user = _user_or_404(user_id)
    return jsonify(serializers.user_detail(user, Task.list_by_user(user_id))), 200


def create_user():
    data = validators.json_body()
    fields = validators.user_fields_for_create(data)
    if User.get_by_email(fields['email']):
        raise ConflictError('Email já cadastrado')
    role = validators.role(data.get('role', ROLE_USER))
    if role != ROLE_USER:
        ensure_role(ROLE_ADMIN)  # only an admin may create privileged accounts
    user = User.create(role=role, **fields)
    logger.info('Usuário criado: %s', user.id)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = _user_or_404(user_id)
    data = validators.json_body()
    fields = {}
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            raise ValidationError('Nome é obrigatório')
        fields['name'] = data['name']
    if 'email' in data:
        email = validators.email(data['email'])
        existing = User.get_by_email(email)
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        fields['email'] = email
    if 'password' in data:
        fields['password'] = validators.password(data['password'], 'Senha muito curta')
    if 'role' in data:
        fields['role'] = validators.role(data['role'])
        ensure_role(ROLE_ADMIN)  # role changes are an admin operation
    if 'active' in data:
        fields['active'] = validators.active_flag(data['active'])
    user.update(fields)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = _user_or_404(user_id)
    user.delete_with_tasks()
    logger.info('Usuário deletado: %s', user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def list_user_tasks(user_id):
    _user_or_404(user_id)
    now = utc_now()
    return jsonify([serializers.user_task_summary(task, now) for task in Task.list_by_user(user_id)]), 200


def login():
    data = validators.json_body()
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')
    user = User.get_by_email(email)
    if user is None or not user.verify_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    return jsonify(serializers.login_payload(user, issue_token(user))), 200
