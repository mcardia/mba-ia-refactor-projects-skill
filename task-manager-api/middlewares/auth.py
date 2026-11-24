"""Signed session tokens issued at login, and the role guard for privileged routes.

The role and the active flag are always read from the database, never from the token or the request.
"""
from functools import wraps

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models.user import User
from utils.errors import ForbiddenError, UnauthorizedError

_BEARER = 'Bearer '


def _signer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='auth-token')


def issue_token(user):
    return _signer().dumps({'uid': user.id})


def current_user():
    header = request.headers.get('Authorization', '')
    if not header.startswith(_BEARER):
        raise UnauthorizedError('Token de autenticação obrigatório')
    try:
        claims = _signer().loads(header[len(_BEARER):],
                                 max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except (BadSignature, SignatureExpired):
        raise UnauthorizedError('Token inválido ou expirado')
    user = User.get_by_id(claims.get('uid')) if isinstance(claims, dict) else None
    if user is None or not user.active:
        raise UnauthorizedError('Token inválido ou expirado')
    return user


def ensure_role(role):
    """401 without a valid session, 403 when the authenticated user lacks the role."""
    user = current_user()
    if user.role != role:
        raise ForbiddenError('Permissão insuficiente')
    return user


def require_role(role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            ensure_role(role)
            return view(*args, **kwargs)
        return wrapper
    return decorator
