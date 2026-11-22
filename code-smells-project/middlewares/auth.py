"""Admin guard: requires the X-Admin-Token header to match the configured ADMIN_TOKEN."""
import hmac
from functools import wraps

from flask import current_app, request

from utils.errors import ForbiddenError, UnauthorizedError


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config["ADMIN_TOKEN"]
        if not expected:
            raise ForbiddenError("Endpoint desabilitado")
        supplied = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(supplied.encode(), expected.encode()):
            raise UnauthorizedError("Token de administrador obrigatório")
        return view(*args, **kwargs)
    return wrapper
