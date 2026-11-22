import logging

from flask import current_app, jsonify

from config.constants import ROLE_USER
from controllers import validators
from database import commit
from middlewares.auth import require_admin_user, require_user
from models import Task, User
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

EMAIL_TAKEN = 'Email já cadastrado'


def _user_or_404(user_id):
    user = User.get(user_id)
    if user is None:
        raise NotFoundError(validators.USER_NOT_FOUND)
    return user


def _ensure_email_free(email, current_user_id=None):
    existing = User.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError(EMAIL_TAKEN)


def list_users():
    task_totals = Task.totals_by_user()
    result = []
    for user in User.all():
        data = user.to_dict()
        data['task_count'] = task_totals.get(user.id, (0, 0))[0]
        result.append(data)
    return jsonify(result), 200


def get_user(user_id):
    user = _user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.for_user(user_id)]
    return jsonify(data), 200


def create_user():
    data = validators.json_body()
    role = data.get('role', ROLE_USER)
    if role != ROLE_USER:  # only an administrator may create privileged accounts
        require_admin_user()

    if not data.get('name'):
        raise ValidationError(validators.NAME_REQUIRED)
    if not data.get('email'):
        raise ValidationError('Email é obrigatório')
    if not data.get('password'):
        raise ValidationError('Senha é obrigatória')
    name = validators.name(data['name'])
    email = validators.email(data['email'])
    password = validators.password(data['password'], 'Senha deve ter no mínimo 4 caracteres')
    _ensure_email_free(email)
    role = validators.role(role)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    user.add()
    commit('Erro ao criar usuário', conflict_message=EMAIL_TAKEN)
    logger.info('Usuário criado: %s', user.id)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    requester = require_user()
    if not requester.is_admin() and requester.id != user_id:
        raise ForbiddenError('Acesso negado')
    user = _user_or_404(user_id)
    data = validators.json_body()

    if 'name' in data:
        user.name = validators.name(data['name'])
    if 'email' in data:
        user.email = validators.email(data['email'])
        _ensure_email_free(user.email, current_user_id=user_id)
    if 'password' in data:
        user.set_password(validators.password(data['password'], 'Senha muito curta'))
    if 'role' in data:
        new_role = validators.role(data['role'])
        if new_role != user.role and not requester.is_admin():
            raise ForbiddenError('Acesso restrito a administradores')
        user.role = new_role
    if 'active' in data:
        user.active = validators.active_flag(data['active'])

    commit('Erro ao atualizar', conflict_message=EMAIL_TAKEN)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    _user_or_404(user_id).remove()  # cascades to the user's tasks in the same transaction
    commit('Erro ao deletar')
    logger.info('Usuário deletado: %s', user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def list_user_tasks(user_id):
    _user_or_404(user_id)
    return jsonify([task.to_user_task_dict() for task in Task.for_user(user_id)]), 200


def login():
    data = validators.json_body()
    email, password = data.get('email'), data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    commit('Erro ao autenticar')  # persists a legacy-hash upgrade, if one happened
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': current_app.extensions['token_service'].issue(user),
    }), 200
