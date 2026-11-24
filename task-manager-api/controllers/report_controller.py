from flask import jsonify

from models.user import User
from services import report_service
from utils.errors import NotFoundError


def summary_report():
    return jsonify(report_service.summary()), 200


def user_report(user_id):
    user = User.get_by_id(user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return jsonify(report_service.user_report(user)), 200
