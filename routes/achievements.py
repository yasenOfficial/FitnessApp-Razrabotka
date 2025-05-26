from flask import render_template, redirect, make_response
from flask_jwt_extended import jwt_required, create_access_token
from utils.helpers import get_current_user
from . import achievements_bp

@achievements_bp.route('/')
@jwt_required()
def achievements():
    user = get_current_user()
    if not user:
        return redirect('/auth')

    user.calculate_achievements()
    response = make_response(render_template('achievements.html', user=user))
    new_token = create_access_token(identity=user.id)
    response.set_cookie(
        'access_token_cookie',
        new_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=900  # 15 minutes
    )
    return response 