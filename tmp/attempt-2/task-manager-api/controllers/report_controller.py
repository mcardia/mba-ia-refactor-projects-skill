from flask import jsonify

from controllers import validators
from models import User
from services import report_service
from utils.errors import NotFoundError


def summary_report():
    return jsonify(report_service.summary_report()), 200


def user_report(user_id):
    user = User.get(user_id)
    if user is None:
        raise NotFoundError(validators.USER_NOT_FOUND)
    return jsonify(report_service.user_report(user)), 200
