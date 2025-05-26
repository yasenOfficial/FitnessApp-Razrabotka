from datetime import datetime
from extensions import db


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_type = db.Column(db.String(20), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    intensity = db.Column(db.Float, default=1.0)
    points = db.Column(db.Integer, default=0)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', back_populates='exercises')

    def __repr__(self):
        return f'<Exercise {self.exercise_type} - {self.count}>'
