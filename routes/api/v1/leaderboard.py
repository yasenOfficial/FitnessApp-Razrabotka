from flask import jsonify, request
from flask_jwt_extended import jwt_required
from models import User
from . import api_v1


@api_v1.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    pagination = User.query.order_by(User.exercise_points.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'items': [
            {
                'rank': (page - 1) * per_page + idx + 1,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'exercise_points': user.exercise_points
                },
                'points': user.exercise_points
            }
            for idx, user in enumerate(pagination.items)
        ],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })
