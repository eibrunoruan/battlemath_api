from flask import Blueprint, jsonify
from app.models import Badge

bp = Blueprint('badges', __name__, url_prefix='/badges')

@bp.route('', methods=['GET'])
def list_badges():
    badges = Badge.query.all()
    return jsonify([badge.to_dict() for badge in badges]), 200
