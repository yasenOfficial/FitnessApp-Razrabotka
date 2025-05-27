from flask import redirect, render_template, send_from_directory
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from utils.helpers import get_current_user

from . import main_bp


@main_bp.route("/")
def index():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        if user_id:
            return redirect("/dashboard")
    except:
        pass
    return render_template("home.html")


@main_bp.route("/static/<path:p>")
def static_serve(p):
    return send_from_directory("static", p)
