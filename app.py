
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import os
from sqlalchemy import desc

app = Flask(__name__, static_folder='static')
# Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamefit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=30)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # For simplicity, not using CSRF protection

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    exercise_points = db.Column(db.Integer, default=0)
    join_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    achievements_unlocked = db.Column(db.Integer, default=0)
    
    # Relationship
    exercises = db.relationship('Exercise', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_rank(self):
        pts = self.exercise_points
        if pts >= 1000: return 'Master'
        if pts >= 700: return 'Ruby'
        if pts >= 400: return 'Diamond'
        if pts >= 200: return 'Silver'
        return 'Bronze'
    
    def calculate_achievements(self):
        # Calculate how many achievements unlocked based on points
        count = 0
        if self.exercise_points >= 10: count += 1
        if self.exercise_points >= 50: count += 1
        if self.exercise_points >= 100: count += 1
        if self.exercise_points >= 200: count += 1
        if self.exercise_points >= 300: count += 1
        if self.exercise_points >= 400: count += 1
        if self.exercise_points >= 500: count += 1
        if self.exercise_points >= 700: count += 1
        if self.exercise_points >= 1000: count += 1
        # Special achievements will be added later
        self.achievements_unlocked = count
        db.session.commit()

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    intensity = db.Column(db.Float, nullable=False, default=1.0)
    points = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Helper Functions
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        if current_user_id:
            return User.query.get(current_user_id)
    except:
        pass
    return None

# Routes
@app.route('/')
def home():
    user = get_current_user()
    return render_template('home.html', user=user)

@app.route('/auth')
def auth_page():
    return render_template('auth.html')

@app.route('/leaderboard')
def leaderboard():
    user = get_current_user()
    top_players = User.query.order_by(desc(User.exercise_points)).limit(20).all()
    
    # Find user's rank
    user_rank = 0
    if user:
        all_users = User.query.order_by(desc(User.exercise_points)).all()
        for i, u in enumerate(all_users):
            if u.id == user.id:
                user_rank = i + 1
                break
    
    return render_template('leaderboard.html', user=user, top_players=top_players, user_rank=user_rank)

@app.route('/achievements')
def achievements():
    user = get_current_user()
    if user:
        user.calculate_achievements()
    return render_template('achievements.html', user=user)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 409
    
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Registered successfully'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        response = jsonify({'success': True, 'message': 'Login successful'})
        response.set_cookie('access_token', access_token, httponly=True, max_age=30*24*60*60)  # 30 days
        return response
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/log-exercise', methods=['POST'])
@jwt_required()
def log_exercise():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    data = request.get_json()
    exercise_type = data.get('exercise_type')
    count = int(data.get('count', 0))
    intensity = float(data.get('intensity', 1.0))
    points = int(data.get('points', 0))
    
    if not exercise_type or count <= 0:
        return jsonify({'success': False, 'message': 'Invalid exercise data'}), 400
    
    # Create exercise record
    exercise = Exercise(
        user_id=current_user_id,
        exercise_type=exercise_type,
        count=count,
        intensity=intensity,
        points=points
    )
    
    # Update user points
    user.exercise_points += points
    
    db.session.add(exercise)
    db.session.commit()
    
    # Update achievements
    user.calculate_achievements()
    
    return jsonify({
        'success': True,
        'message': f'Exercise logged! You earned {points} points!',
        'new_total': user.exercise_points,
        'rank': user.get_rank()
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    response = jsonify({'success': True, 'message': 'Logged out successfully'})
    response.delete_cookie('access_token')
    return response

@app.route('/api/delete', methods=['DELETE'])
@jwt_required()
def api_delete():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user:
        db.session.delete(user)
        db.session.commit()
        response = jsonify({'success': True, 'message': 'User deleted'})
        response.delete_cookie('access_token')
        return response
    
    return jsonify({'success': False, 'message': 'User not found'}), 404

# Serve static files
@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/css'), filename)

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/js'), filename)

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/images'), filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)