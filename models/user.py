from datetime import datetime

from extensions import bcrypt, db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    exercise_points = db.Column(db.Integer, default=0)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    achievements_unlocked = db.Column(db.Integer, default=0)
    exercises = db.relationship("Exercise", back_populates="user", lazy=True)
    achievements = db.relationship("Achievement", back_populates="user", lazy=True)

    def set_password(self, pw):
        self.password_hash = bcrypt.generate_password_hash(pw).decode()

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password_hash, pw)

    def get_rank(self):
        pts = self.exercise_points
        if pts >= 1000:
            return "Master"
        if pts >= 700:
            return "Ruby"
        if pts >= 400:
            return "Diamond"
        if pts >= 200:
            return "Silver"
        return "Bronze"

    def calculate_achievements(self):
        """Calculate and update user achievements based on exercise history"""
        from models import Achievement

        # Example achievement thresholds
        achievement_thresholds = {
            "Beginner": 100,
            "Intermediate": 500,
            "Advanced": 1000,
            "Expert": 5000,
            "Master": 10000,
        }

        # Check points-based achievements
        for name, threshold in achievement_thresholds.items():
            if self.exercise_points >= threshold:
                # Check if achievement already exists
                existing = Achievement.query.filter_by(user_id=self.id, name=name).first()

                if not existing:
                    achievement = Achievement(
                        user_id=self.id,
                        name=name,
                        description=f"Earned {threshold} exercise points",
                    )
                    db.session.add(achievement)

        db.session.commit()
