from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import User


def get_current_user():
    try:
        uid = get_jwt_identity()
        return db.session.get(User, uid) if uid else None
    except Exception:  # Catch any exception but log it properly
        return None
