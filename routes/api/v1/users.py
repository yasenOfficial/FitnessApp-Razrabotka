from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from extensions import db, bcrypt
from . import api_v1


@api_v1.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    if not all(k in data for k in ("username", "email", "password")):
        return jsonify({"code": 400, "message": "Missing required fields"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"code": 400, "message": "Username already exists"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"code": 400, "message": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(
        username=data["username"], email=data["email"], password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return (
        jsonify(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "exercise_points": user.exercise_points,
                "achievements": [],
            }
        ),
        201,
    )


@api_v1.route("/users/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "exercise_points": user.exercise_points,
            "achievements": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "unlocked_at": a.unlocked_at.isoformat() if a.unlocked_at else None,
                }
                for a in user.achievements
            ],
        }
    )


@api_v1.route("/users/me/achievements", methods=["GET"])
@jwt_required()
def get_user_achievements():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    return jsonify(
        [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "unlocked_at": a.unlocked_at.isoformat() if a.unlocked_at else None,
            }
            for a in user.achievements
        ]
    )
