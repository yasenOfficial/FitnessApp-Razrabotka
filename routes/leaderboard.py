from flask import make_response, redirect, render_template
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy import desc

from models import User
from utils.helpers import get_current_user

from . import leaderboard_bp


@leaderboard_bp.route("/")
@jwt_required()
def leaderboard():
    user = get_current_user()
    if not user:
        return redirect("/auth")

    top_players = User.query.order_by(desc(User.exercise_points)).limit(20).all()
    all_users = User.query.order_by(desc(User.exercise_points)).all()
    user_rank = next((i + 1 for i, u in enumerate(all_users) if u.id == user.id), 0)

    response = make_response(
        render_template("leaderboard.html", user=user, top_players=top_players, user_rank=user_rank)
    )
    new_token = create_access_token(identity=user.id)
    response.set_cookie(
        "access_token_cookie",
        new_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=900,  # 15 minutes
    )
    return response
