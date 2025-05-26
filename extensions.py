from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()

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