"""Domain exceptions. Raised by any layer, translated to HTTP by middlewares.error_handler."""


class AppError(Exception):
    status = 500

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ValidationError(AppError):
    status = 400


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409
