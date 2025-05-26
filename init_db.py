from extensions import db
from models import User, Exercise
from app import create_app

def init_database():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database() 