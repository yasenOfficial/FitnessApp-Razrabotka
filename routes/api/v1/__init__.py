from flask import Blueprint

# Create the blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

def register_routes():
    """Register all routes with the api_v1 blueprint."""
    # Import routes here to avoid circular imports
    from . import users, exercises, auth, leaderboard
