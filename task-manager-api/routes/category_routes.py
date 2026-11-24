from flask import Blueprint

from config.constants import ROLE_ADMIN
from controllers import category_controller
from middlewares.auth import require_role

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return category_controller.list_categories()


@category_bp.route('/categories', methods=['POST'])
def create_category():
    return category_controller.create_category()


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    return category_controller.update_category(category_id)


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@require_role(ROLE_ADMIN)
def delete_category(category_id):
    return category_controller.delete_category(category_id)
