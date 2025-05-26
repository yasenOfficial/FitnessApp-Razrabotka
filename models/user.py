from datetime import datetime
from extensions import db, bcrypt

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    exercise_points = db.Column(db.Integer, default=0)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    achievements_unlocked = db.Column(db.Integer, default=0)
    exercises = db.relationship('Exercise', backref='user', lazy=True)

    def set_password(self, pw):
        self.password_hash = bcrypt.generate_password_hash(pw).decode()

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password_hash, pw)

    def get_rank(self):
        pts = self.exercise_points
        if pts >= 1000: return 'Master'
        if pts >= 700:  return 'Ruby'
        if pts >= 400:  return 'Diamond'
        if pts >= 200:  return 'Silver'
        return 'Bronze'

    def calculate_achievements(self):
        thresholds = [10,50,100,200,300,400,500,700,1000]
        self.achievements_unlocked = sum(self.exercise_points>=t for t in thresholds)
        db.session.commit() 