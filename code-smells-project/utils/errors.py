"""Domain exceptions. Every layer may raise them; the error handler maps them to HTTP."""


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
