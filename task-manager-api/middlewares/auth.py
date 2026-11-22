"""Minimal admin guard for privileged/destructive operations (X-Admin-Token header)."""
import hmac
from functools import wraps

from flask import current_app, request

from utils.errors import ForbiddenError, UnauthorizedError


def ensure_admin():
    expected = current_app.config.get('ADMIN_TOKEN', '')
    if not expected:
        raise ForbiddenError('Endpoint desabilitado')
    supplied = request.headers.get('X-Admin-Token', '')
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise UnauthorizedError('Token de administrador obrigatório')


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        ensure_admin()
        return view(*args, **kwargs)
    return wrapper
