from flask import jsonify, request
from flask_jwt_extended import create_access_token
from models import User
from extensions import bcrypt
from . import api_v1

@api_v1.route('/auth/token', methods=['POST'])
def get_token():
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'code': 400, 'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer'
        })
    
    return jsonify({'code': 401, 'message': 'Invalid username or password'}), 401 