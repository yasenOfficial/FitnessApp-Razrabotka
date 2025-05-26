from flask import render_template, request, jsonify, redirect, url_for, current_app, flash
from flask_jwt_extended import create_access_token
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from extensions import db, mail
from models import User
from utils.validators import validate_username, validate_password, validate_email, sanitize_input
from . import auth_bp
from werkzeug.security import generate_password_hash, check_password_hash

@auth_bp.route('/')
def auth_page():
    confirmed = request.args.get('confirmed')
    return render_template('auth.html', confirmed=bool(confirmed))

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = current_app.ts.loads(token, salt='email-confirm', max_age=3600)
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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        email = sanitize_input(request.form.get('email'))
        password = request.form.get('password')
        
        # Validate inputs
        if not validate_username(username):
            flash('Invalid username format. Use only letters, numbers, and underscores (3-30 characters).', 'error')
            return render_template('auth/register.html')
            
        if not validate_email(email):
            flash('Invalid email format.', 'error')
            return render_template('auth/register.html')
            
        if not validate_password(password):
            flash('Password must be at least 8 characters and contain uppercase, lowercase, and numbers.', 'error')
            return render_template('auth/register.html')

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')

        # Create new user with hashed password
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username'))
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # Set session or JWT token here
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.index'))
            
        flash('Invalid username or password.', 'error')
        return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/api/register', methods=['POST'])
def register_api():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify(success=False, message='All fields required'), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(success=False, message='Username or email taken'), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = current_app.ts.dumps(email, salt='email-confirm')
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    
    msg = Message(
        "Confirm your GameFit account",
        recipients=[email]
    )
    msg.body = f"Hi {username}, confirm here:\n\n{confirm_url}"
    
    try:
        mail.send(msg)
    except Exception as ex:
        current_app.logger.error(f"Mail failed: {ex}")

    return jsonify(success=True, message='Registered! Check your email.'), 200

@auth_bp.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify(success=False, message='Invalid credentials'), 401
    if not user.is_active:
        return jsonify(success=False, message='Please confirm email'), 403

    token = create_access_token(identity=user.id)
    response = jsonify(success=True, message='Login successful')
    response.set_cookie(
        current_app.config['JWT_ACCESS_COOKIE_NAME'],
        token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=900  # 15 minutes
    )
    return response

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    response = jsonify(success=True)
    response.delete_cookie(current_app.config['JWT_ACCESS_COOKIE_NAME'])
    return response 