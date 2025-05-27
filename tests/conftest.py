import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from extensions import db, mail
from routes import register_blueprints
import os

@pytest.fixture
def app():
    # Get the absolute path to the project root directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_dir, 'templates')
    static_dir = os.path.join(project_dir, 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test_secret_key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test_jwt_secret',
        'JWT_TOKEN_LOCATION': ['cookies'],
        'JWT_COOKIE_CSRF_PROTECT': False,
        'JWT_ACCESS_COOKIE_NAME': 'access_token_cookie',
        'JWT_ACCESS_TOKEN_EXPIRES': False,  # Tokens never expire in testing
        'JWT_COOKIE_SECURE': False,  # Allow non-HTTPS cookies in testing
        'JWT_SESSION_COOKIE': False
    })

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    JWTManager(app)

    # Register blueprints using the proper registration function
    register_blueprints(app)
    
    # Debug print to check registered routes
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    # Create tables
    with app.app_context():
        db.create_all()

    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner() 