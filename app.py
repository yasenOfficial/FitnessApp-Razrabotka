from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, redirect, make_response, url_for
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv
import datetime, os
from sqlalchemy import desc

# Load env
load_dotenv()

app = Flask(__name__, static_folder='static')

# --- Configuration ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(
    minutes=int(os.getenv('JWT_EXPIRES_MINUTES', 15))
)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

# **Use a consistent cookie name for JWT**
app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token_cookie'

# Mail settings
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = (
    os.getenv('MAIL_DEFAULT_NAME'), os.getenv('MAIL_DEFAULT_EMAIL')
)
app.config['MAIL_DEBUG'] = True  # log mail actions

# Extensions
db    = SQLAlchemy(app)
bcrypt= Bcrypt(app)
jwt   = JWTManager(app)
mail  = Mail(app)
ts    = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Ensure the JWT "sub" (subject) is always a string
@jwt.user_identity_loader
def user_identity_lookup(identity):
    return str(identity)


# --- Models ---
class User(db.Model):
    id                 = db.Column(db.Integer, primary_key=True)
    username           = db.Column(db.String(80), unique=True, nullable=False)
    email              = db.Column(db.String(120), unique=True, nullable=False)
    password_hash      = db.Column(db.String(128), nullable=False)
    is_active          = db.Column(db.Boolean, default=False)
    exercise_points    = db.Column(db.Integer, default=0)
    join_date          = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    achievements_unlocked = db.Column(db.Integer, default=0)
    exercises          = db.relationship('Exercise', backref='user', lazy=True)

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


class Exercise(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_type = db.Column(db.String(50), nullable=False)
    count         = db.Column(db.Integer, nullable=False)
    intensity     = db.Column(db.Float, nullable=False, default=1.0)
    points        = db.Column(db.Integer, nullable=False)
    date_added    = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# --- Helpers ---
def get_current_user():
    try:
        uid = get_jwt_identity()
        return User.query.get(uid) if uid else None
    except:
        return None


# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html', user=get_current_user())


@app.route('/auth')
def auth_page():
    confirmed = request.args.get('confirmed')
    return render_template('auth.html', confirmed=bool(confirmed))


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = ts.loads(
            token,
            salt='email-confirm',
            max_age=int(os.getenv('CONFIRM_EXPIRATION', 3600))
        )
    except SignatureExpired:
        return "Link expired", 400
    except BadSignature:
        return "Invalid token", 400

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_active = True
        db.session.commit()
        return redirect('/auth?confirmed=1')
    return "User not found", 404


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username, email, pw = data.get('username'), data.get('email'), data.get('password')
    if not all([username, email, pw]):
        return jsonify(success=False, message='All fields required'), 400

    if User.query.filter((User.username==username)|(User.email==email)).first():
        return jsonify(success=False, message='Username or email taken'), 409

    # Create inactive user
    user = User(username=username, email=email)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()

    # Send confirmation email
    token = ts.dumps(email, salt='email-confirm')
    link  = url_for('confirm_email', token=token, _external=True)
    msg   = Message("Confirm your GameFit account", recipients=[email])
    msg.body = f"Hi {username}, please confirm here:\n\n{link}"
    try:
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Mail failed: {e}")

    return jsonify(success=True, message='Registered! Check your email.'), 200


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username, pw = data.get('username'), data.get('password')
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(pw):
        return jsonify(success=False, message='Invalid credentials'), 401
    if not user.is_active:
        return jsonify(success=False, message='Please confirm email'), 403

    token = create_access_token(identity=user.id)
    resp  = jsonify(success=True, message='Login successful')
    resp.set_cookie(
        app.config['JWT_ACCESS_COOKIE_NAME'],  # access_token_cookie
        token,
        httponly=True,
        max_age=int(os.getenv('JWT_EXPIRES_MINUTES', 15)) * 60
    )
    return resp


@app.route('/leaderboard')
@jwt_required()
def leaderboard():
    user = get_current_user() or redirect('/auth')
    players = User.query.order_by(desc(User.exercise_points)).limit(20).all()
    all_u   = User.query.order_by(desc(User.exercise_points)).all()
    rank    = next((i+1 for i,u in enumerate(all_u) if u.id==user.id), 0)

    resp    = make_response(
        render_template('leaderboard.html', user=user,
                        top_players=players, user_rank=rank)
    )
    # refresh session
    new_token = create_access_token(identity=user.id)
    resp.set_cookie(
        app.config['JWT_ACCESS_COOKIE_NAME'],
        new_token,
        httponly=True,
        max_age=int(os.getenv('JWT_EXPIRES_MINUTES', 15)) * 60
    )
    return resp


@app.route('/achievements')
@jwt_required()
def achievements():
    user = get_current_user() or redirect('/auth')
    user.calculate_achievements()

    resp = make_response(render_template('achievements.html', user=user))
    new_token = create_access_token(identity=user.id)
    resp.set_cookie(
        app.config['JWT_ACCESS_COOKIE_NAME'],
        new_token,
        httponly=True,
        max_age=int(os.getenv('JWT_EXPIRES_MINUTES', 15)) * 60
    )
    return resp


@app.route('/api/log-exercise', methods=['POST'])
@jwt_required()
def log_exercise():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        return jsonify(success=False, message='User not found'), 404

    d   = request.get_json()
    ex  = d.get('exercise_type')
    cnt = int(d.get('count', 0))
    inty = float(d.get('intensity', 1.0))
    pts = int(d.get('points', 0))

    if not ex or cnt <= 0:
        return jsonify(success=False, message='Invalid data'), 400

    e = Exercise(
        user_id=uid,
        exercise_type=ex,
        count=cnt,
        intensity=inty,
        points=pts
    )
    user.exercise_points += pts
    db.session.add(e)
    db.session.commit()
    user.calculate_achievements()

    resp = make_response(jsonify(
        success=True,
        message=f'Logged {pts} points!',
        new_total=user.exercise_points,
        rank=user.get_rank()
    ))
    # refresh session
    new_token = create_access_token(identity=uid)
    resp.set_cookie(
        app.config['JWT_ACCESS_COOKIE_NAME'],
        new_token,
        httponly=True,
        max_age=int(os.getenv('JWT_EXPIRES_MINUTES', 15)) * 60
    )
    return resp


@app.route('/api/logout', methods=['POST'])
def logout():
    r = jsonify(success=True, message='Logged out')
    r.delete_cookie(app.config['JWT_ACCESS_COOKIE_NAME'])
    return r


@app.route('/api/delete', methods=['DELETE'])
@jwt_required()
def api_delete():
    uid  = get_jwt_identity()
    user = User.query.get(uid)
    if user:
        db.session.delete(user)
        db.session.commit()
        r = jsonify(success=True, message='Deleted')
        r.delete_cookie(app.config['JWT_ACCESS_COOKIE_NAME'])
        return r
    return jsonify(success=False, message='Not found'), 404


@app.route('/profile')
@jwt_required()
def profile():
    user = get_current_user() or redirect('/auth')
    resp = make_response(render_template('profile.html', user=user))
    # refresh session
    new_token = create_access_token(identity=user.id)
    resp.set_cookie(
        app.config['JWT_ACCESS_COOKIE_NAME'],
        new_token,
        httponly=True,
        max_age=int(os.getenv('JWT_EXPIRES_MINUTES', 15)) * 60
    )
    return resp

@app.route('/profile/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_profile():
    user = get_current_user()
    if not user:
        return redirect('/auth')

    if request.method == 'POST':
        data = request.form
        new_username = data.get('username').strip()
        new_email    = data.get('email').strip()
        new_password = data.get('password').strip()

        # basic validation
        if not new_username or not new_email:
            error = "Username and email cannot be empty."
            return render_template('profile_edit.html', user=user, error=error)

        # check uniqueness
        if new_username != user.username and User.query.filter_by(username=new_username).first():
            error = "That username is already taken."
            return render_template('profile_edit.html', user=user, error=error)

        if new_email != user.email and User.query.filter_by(email=new_email).first():
            error = "That email is already in use."
            return render_template('profile_edit.html', user=user, error=error)

        # apply changes
        user.username = new_username
        user.email    = new_email
        if new_password:
            user.set_password(new_password)
        db.session.commit()

        return redirect('/profile')

    # GET — render form
    return render_template('profile_edit.html', user=user)


# Static files
@app.route('/static/<path:p>')
def static_serve(p):
    return send_from_directory('static', p)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
