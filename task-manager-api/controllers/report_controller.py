"""Report use cases."""
from models.user import User
from services import report_service
from utils.errors import NotFoundError


def task_stats():
    return report_service.task_stats()


def summary_report():
    return report_service.summary_report()


def user_report(user_id):
    user = User.find(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return report_service.user_report(user)
