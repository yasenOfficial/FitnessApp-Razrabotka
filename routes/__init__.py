from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
achievements_bp = Blueprint('achievements', __name__, url_prefix='/achievements')
leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

# List of all blueprints
blueprints = [
    auth_bp,
    main_bp,
    dashboard_bp,
    achievements_bp,
    profile_bp,
    leaderboard_bp
]


def register_blueprints(app):
    """Register all blueprints with the app."""
    # Import routes here to avoid circular imports
    # These imports are required to register the routes with the blueprints
    from . import main
    from . import auth
    from . import dashboard
    from . import profile
    from . import achievements
    from . import leaderboard

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
