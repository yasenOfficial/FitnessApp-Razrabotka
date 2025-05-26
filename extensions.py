from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_talisman import Talisman

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()
talisman = Talisman()


def init_extensions(app):
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # Create URL safe time serializer
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    app.ts = ts  # Attach to app for access in routes

    # JWT configuration
    @jwt.unauthorized_loader
    def handle_unauthorized_loader(msg):
        return redirect(url_for("auth.auth_page"))

    @jwt.invalid_token_loader
    def handle_invalid_token(msg):
        return redirect(url_for("auth.auth_page"))

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_data):
        return redirect(url_for("auth.auth_page"))

    @jwt.needs_fresh_token_loader
    def handle_fresh_token_required(jwt_header, jwt_data):
        return redirect(url_for("auth.auth_page"))

    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_data):
        return redirect(url_for("auth.auth_page"))

    @jwt.user_identity_loader
    def user_identity_lookup(identity):
        return str(identity)


def init_security(app):
    # Enable Talisman security headers
    talisman.init_app(
        app,
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True,
        content_security_policy={
            "default-src": "'self'",
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https:", "data:"],
        },
    )
