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
    ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    app.ts = ts  # Attach to app for access in routes
    
    # JWT identity loader
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
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", 'data:', 'https:'],
            'font-src': ["'self'", 'https:', 'data:'],
        }
    ) 