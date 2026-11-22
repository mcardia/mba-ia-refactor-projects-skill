"""Minimal guard for privileged endpoints: X-Admin-Token header checked against config."""
import hmac
from functools import wraps

from flask import current_app, request

from utils.errors import ForbiddenError, UnauthorizedError


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        if not esperado:
            raise ForbiddenError("Endpoint administrativo desabilitado")
        informado = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(informado.encode(), esperado.encode()):
            raise UnauthorizedError("Token de administrador inválido ou ausente")
        return view(*args, **kwargs)
    return wrapper
