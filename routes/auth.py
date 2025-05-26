from flask import render_template, request, jsonify, redirect, url_for, current_app
from flask_jwt_extended import create_access_token
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from extensions import db, mail
from models import User
from . import auth_bp

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

@auth_bp.route('/api/register', methods=['POST'])
def register():
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
def login():
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