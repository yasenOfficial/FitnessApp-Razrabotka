from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
achievements_bp = Blueprint('achievements', __name__, url_prefix='/achievements')
leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

# Import routes AFTER blueprint creation to avoid circular imports
from .main import *
from .auth import *
from .dashboard import *
from .profile import *
from .achievements import *
from .leaderboard import *

# List of all blueprints to register
blueprints = [
    main_bp,
    auth_bp,
    dashboard_bp,
    profile_bp,
    achievements_bp,
    leaderboard_bp
] 