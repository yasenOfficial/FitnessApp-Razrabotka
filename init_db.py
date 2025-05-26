from extensions import db
from models import User, Exercise, Achievement
from app import create_app

def init_database():
    app = create_app()
    with app.app_context():
        # Drop all tables first to ensure clean state
        db.drop_all()
        # Create all database tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database() 