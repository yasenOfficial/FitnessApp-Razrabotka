from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, redirect, make_response, url_for, flash
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
# consistent cookie name
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
app.config['MAIL_DEBUG'] = True

# Extensions
db    = SQLAlchemy(app)
bcrypt= Bcrypt(app)
jwt   = JWTManager(app)
mail  = Mail(app)
ts    = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Ensure JWT sub is string
@jwt.user_identity_loader
def user_identity_lookup(identity):
    return str(identity)

# Models
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

# Helpers
def get_current_user():
    try:
        uid = get_jwt_identity()
        return User.query.get(uid) if uid else None
    except:
        return None

# Dashboard-specific rank thresholds
EXERCISE_RANKS = {
    'pushup': [(2000,'Mythic'),(1000,'Master'),(700,'Ruby'),(400,'Diamond'),(200,'Silver'),(0,'Bronze')],
    'situp':  [(3000,'Mythic'),(1500,'Master'),(1000,'Ruby'),(500,'Diamond'), (200,'Silver'),(0,'Bronze')],
    'squat':  [(2500,'Mythic'),(1200,'Master'),(800,'Ruby'), (500,'Diamond'), (200,'Silver'),(0,'Bronze')],
    'burpee': [(1000,'Mythic'),(700,'Master'), (400,'Ruby'),  (200,'Diamond'), (100,'Silver'),(0,'Bronze')],
    'run':    [(5000,'Mythic'),(2000,'Master'),(1000,'Ruby'), (500,'Diamond'), (200,'Silver'),(0,'Bronze')],
}

# Routes
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
        email = ts.loads(token, salt='email-confirm', max_age=int(os.getenv('CONFIRM_EXPIRATION',3600)))
    except SignatureExpired:
        return "Link expired",400
    except BadSignature:
        return "Invalid token",400
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_active=True; db.session.commit()
        return redirect('/auth?confirmed=1')
    return "User not found",404

@app.route('/api/register',methods=['POST'])
def api_register():
    d=request.get_json();u,e,p=d.get('username'),d.get('email'),d.get('password')
    if not all([u,e,p]): return jsonify(success=False,message='All fields required'),400
    if User.query.filter((User.username==u)|(User.email==e)).first():
        return jsonify(success=False,message='Username or email taken'),409
    user=User(username=u,email=e);user.set_password(p)
    db.session.add(user);db.session.commit()
    token=ts.dumps(e,salt='email-confirm')
    link=url_for('confirm_email',token=token,_external=True)
    msg=Message("Confirm your GameFit account",recipients=[e])
    msg.body=f"Hi {u}, confirm here:\n\n{link}"
    try: mail.send(msg)
    except Exception as ex: app.logger.error(f"Mail failed: {ex}")
    return jsonify(success=True,message='Registered! Check your email.'),200

@app.route('/api/login',methods=['POST'])
def api_login():
    d=request.get_json();u,p=d.get('username'),d.get('password')
    user=User.query.filter_by(username=u).first()
    if not user or not user.check_password(p):
        return jsonify(success=False,message='Invalid credentials'),401
    if not user.is_active:
        return jsonify(success=False,message='Please confirm email'),403
    tok=create_access_token(identity=user.id)
    r=jsonify(success=True,message='Login successful')
    r.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'],tok,httponly=True,
                 max_age=int(os.getenv('JWT_EXPIRES_MINUTES',15))*60)
    return r

@app.route('/leaderboard')
@jwt_required()
def leaderboard():
    user=get_current_user() or redirect('/auth')
    players=User.query.order_by(desc(User.exercise_points)).limit(20).all()
    all_u=User.query.order_by(desc(User.exercise_points)).all()
    rank=next((i+1 for i,u in enumerate(all_u) if u.id==user.id),0)
    resp=make_response(render_template('leaderboard.html',user=user,top_players=players,user_rank=rank))
    nt=create_access_token(identity=user.id)
    resp.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'],nt,httponly=True,
                    max_age=int(os.getenv('JWT_EXPIRES_MINUTES',15))*60)
    return resp

@app.route('/achievements')
@jwt_required()
def achievements():
    user=get_current_user() or redirect('/auth')
    user.calculate_achievements()
    resp=make_response(render_template('achievements.html',user=user))
    nt=create_access_token(identity=user.id)
    resp.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'],nt,httponly=True,
                    max_age=int(os.getenv('JWT_EXPIRES_MINUTES',15))*60)
    return resp

@app.route('/api/log-exercise',methods=['POST'])
@jwt_required()
def log_exercise():
    uid=get_jwt_identity();user=User.query.get(uid)
    if not user: return jsonify(success=False,message='User not found'),404
    d=request.get_json();ex=d.get('exercise_type');cnt=int(d.get('count',0));
    pts=int(d.get('points',0));
    if not ex or cnt<=0: return jsonify(success=False,message='Invalid data'),400
    e=Exercise(user_id=uid,exercise_type=ex,count=cnt,intensity=1.0,points=pts)
    user.exercise_points+=pts;db.session.add(e);db.session.commit();user.calculate_achievements()
    resp=make_response(jsonify(success=True,message=f'Logged {pts} points!',new_total=user.exercise_points,rank=user.get_rank()))
    nt=create_access_token(identity=uid)
    resp.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'],nt,httponly=True,
                    max_age=int(os.getenv('JWT_EXPIRES_MINUTES',15))*60)
    return resp

@app.route('/api/logout',methods=['POST'])
def logout():
    r=jsonify(success=True,message='Logged out')
    r.delete_cookie(app.config['JWT_ACCESS_COOKIE_NAME'])
    return r

@app.route('/api/delete',methods=['DELETE'])
@jwt_required()
def api_delete():
    uid=get_jwt_identity();u=User.query.get(uid)
    if u: db.session.delete(u);db.session.commit();r=jsonify(success=True,message='Deleted');r.delete_cookie(app.config['JWT_ACCESS_COOKIE_NAME']);return r
    return jsonify(success=False,message='Not found'),404

@app.route('/profile')
@jwt_required()
def profile():
    user=get_current_user() or redirect('/auth')
    resp=make_response(render_template('profile.html',user=user))
    nt=create_access_token(identity=user.id)
    resp.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'],nt,httponly=True,
                    max_age=int(os.getenv('JWT_EXPIRES_MINUTES',15))*60)
    return resp

@app.route('/profile/edit',methods=['GET','POST'])
@jwt_required()
def edit_profile():
    user=get_current_user() or redirect('/auth')
    if request.method=='POST':
        d=request.form;nu=d.get('username').strip();ne=d.get('email').strip();npw=d.get('password').strip()
        if not nu or not ne: return render_template('profile_edit.html',user=user,error='Username and email cannot be empty.')
        if nu!=user.username and User.query.filter_by(username=nu).first(): return render_template('profile_edit.html',user=user,error='Username already taken')
        if ne!=user.email and User.query.filter_by(email=ne).first(): return render_template('profile_edit.html',user=user,error='Email already in use')
        user.username=nu;user.email=ne
        if npw: user.set_password(npw)
        db.session.commit()
        return redirect('/profile')
    return render_template('profile_edit.html',user=user)

@app.route('/dashboard',methods=['GET','POST'])
@jwt_required()
def dashboard():
    user=get_current_user() or redirect('/auth')
    daily_routine=[{'type':'pushup','label':'Push-ups'},{'type':'situp','label':'Sit-ups'},{'type':'squat','label':'Squats'},{'type':'burpee','label':'Burpees'},{'type':'run','label':'Running (minutes)'}]
    if request.method=='POST':
        logged=False
        for ex in daily_routine:
            cnt=int(request.form.get(ex['type'],0))
            if cnt>0:
                mult={'pushup':0.5,'situp':0.3,'squat':0.4,'pullup':1.0,'burpee':1.5,'plank':0.1,'run':2.0}
                pts=round(mult.get(ex['type'],0.5)*cnt)
                e=Exercise(user_id=user.id,exercise_type=ex['type'],count=cnt,intensity=1.0,points=pts)
                user.exercise_points+=pts;db.session.add(e);logged=True
        if logged: db.session.commit();user.calculate_achievements();flash('Exercises logged!','success')
        else: flash('Enter at least one exercise count.','warning')
        return redirect('/dashboard')
    per_ex_ranks={}
    for ex in daily_routine:
        total=db.session.query(db.func.sum(Exercise.count)).filter_by(user_id=user.id,exercise_type=ex['type']).scalar() or 0
        for thresh,name in EXERCISE_RANKS[ex['type']]:
            if total>=thresh:
                per_ex_ranks[ex['type']]={'total':total,'rank':name}
                break
    return render_template('dashboard.html',user=user,daily_routine=daily_routine,per_ex_ranks=per_ex_ranks)

@app.route('/static/<path:p>')
def static_serve(p):
    return send_from_directory('static',p)

if __name__=='__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)
