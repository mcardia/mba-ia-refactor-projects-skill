"""Authentication guards based on the signed token issued by POST /login."""
from functools import wraps

from flask import current_app, request

from models import User
from utils.errors import ForbiddenError, UnauthorizedError

TOKEN_REQUIRED = 'Token de autenticação obrigatório'
TOKEN_INVALID = 'Token inválido ou expirado'
ADMIN_REQUIRED = 'Acesso restrito a administradores'


def authenticated_user():
    """The user behind the Bearer token, or None when no token was sent."""
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    user_id = current_app.extensions['token_service'].verify(header[len('Bearer '):].strip())
    user = User.get(user_id) if user_id is not None else None
    if user is None or not user.active:
        raise UnauthorizedError(TOKEN_INVALID)
    return user


def require_user():
    user = authenticated_user()
    if user is None:
        raise UnauthorizedError(TOKEN_REQUIRED)
    return user


def require_admin_user():
    user = require_user()
    if not user.is_admin():
        raise ForbiddenError(ADMIN_REQUIRED)
    return user


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_admin_user()
        return view(*args, **kwargs)
    return wrapper
