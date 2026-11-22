"""Minimal admin guard: requires the X-Admin-Token header to match ADMIN_TOKEN."""
import hmac
from functools import wraps

from flask import current_app, request

from utils.errors import ForbiddenError, UnauthorizedError


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config["ADMIN_TOKEN"]
        if not esperado:
            raise ForbiddenError("Endpoint desabilitado")
        informado = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(informado.encode(), esperado.encode()):
            raise UnauthorizedError("Token de administrador obrigatório")
        return view(*args, **kwargs)
    return wrapper
