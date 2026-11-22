from flask import Blueprint

from controllers import category_controller as categories
from middlewares.auth import require_admin

category_bp = Blueprint('categories', __name__)

category_bp.add_url_rule('/categories', view_func=categories.list_categories, methods=['GET'])
category_bp.add_url_rule('/categories', view_func=categories.create_category, methods=['POST'])
category_bp.add_url_rule('/categories/<int:category_id>', view_func=categories.update_category, methods=['PUT'])
category_bp.add_url_rule('/categories/<int:category_id>', view_func=require_admin(categories.delete_category),
                         methods=['DELETE'])
