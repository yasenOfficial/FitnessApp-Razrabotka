from flask import make_response, redirect, render_template, request
from flask_jwt_extended import create_access_token, jwt_required

from extensions import db
from models import User
from utils.helpers import get_current_user

from . import profile_bp


@profile_bp.route("/")
@jwt_required()
def profile():
    user = get_current_user()
    if not user:
        return redirect("/auth")

    response = make_response(render_template("profile.html", user=user))
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


@profile_bp.route("/edit", methods=["GET", "POST"])
@jwt_required()
def edit_profile():
    user = get_current_user()
    if not user:
        return redirect("/auth")

    if request.method == "POST":
        data = request.form
        new_username = data.get("username").strip()
        new_email = data.get("email").strip()
        new_password = data.get("password").strip()

        if not new_username or not new_email:
            return render_template(
                "profile_edit.html",
                user=user,
                error="Username and email cannot be empty.",
            )

        if new_username != user.username and User.query.filter_by(username=new_username).first():
            return render_template("profile_edit.html", user=user, error="Username already taken")

        if new_email != user.email and User.query.filter_by(email=new_email).first():
            return render_template("profile_edit.html", user=user, error="Email already in use")

        user.username = new_username
        user.email = new_email
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        return redirect("/profile")

    return render_template("profile_edit.html", user=user)
