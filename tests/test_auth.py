import pytest
from flask import url_for
import json
from unittest.mock import patch, MagicMock
from models import User
from extensions import db, bcrypt
from werkzeug.security import generate_password_hash

def test_auth_page(client):
    response = client.get('/auth/')
    assert response.status_code == 200

def test_confirm_email_valid(client, app):
    mock_user = MagicMock(
        email="test@example.com",
        is_active=False
    )
    
    with app.app_context():
        # Mock the token validation
        app.ts = MagicMock()
        app.ts.loads.return_value = "test@example.com"
        
        # Mock User.query.filter_by().first()
        with patch('models.User.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = mock_user
            
            response = client.get('/auth/confirm/valid-token')
            
            # Verify the user was activated
            assert mock_user.is_active == True
            assert response.status_code == 302
            assert '/auth?confirmed=1' in response.location

def test_register_api(client, app, test_user_data):
    with app.app_context():
        # Mock the token serializer
        app.ts = MagicMock()
        app.ts.dumps.return_value = "mock-token"

        # Mock the database operations
        with patch('models.User.query') as mock_query, \
             patch('extensions.db.session.add') as mock_add, \
             patch('extensions.db.session.commit') as mock_commit, \
             patch('extensions.mail.send') as mock_send:
            
            # Mock that the user doesn't exist yet
            mock_query.filter.return_value.first.return_value = None
            
            response = client.post('/auth/api/register', 
                                data=json.dumps(test_user_data),
                                content_type='application/json')
            
            assert response.status_code == 200
            assert mock_add.called  # Verify user was added to db
            assert mock_commit.called  # Verify changes were committed
            assert mock_send.called  # Verify confirmation email was sent
            
            response_data = json.loads(response.data)
            assert response_data['success'] == True
            assert 'Registered!' in response_data['message']

def test_login_api(client, test_user_data):
    data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post('/auth/api/login',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code in [200, 401, 403]  # Success or invalid credentials or email not confirmed

def test_logout(client):
    response = client.post('/auth/api/logout')
    assert response.status_code == 200
    assert json.loads(response.data)['success'] == True

def test_register_form(client, app, test_user_data):
    with app.app_context():
        print("\nStarting register form test...")
        
        # Mock User creation and database operations
        with patch('models.User.query') as mock_query, \
             patch('extensions.db.session.add') as mock_add, \
             patch('extensions.db.session.commit') as mock_commit, \
             patch('routes.auth.generate_password_hash') as mock_hash:

            print("Mocks set up...")
            
            # Mock that the user doesn't exist yet
            mock_query.filter_by.return_value.first.return_value = None
            
            # Mock password hashing
            mock_hash.return_value = 'hashed_password'
            
            print("About to make the request...")
            print(f"Request data: {test_user_data}")
            
            response = client.post('/auth/register', data=test_user_data)
            
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data.decode()}")
            print(f"Response location: {response.location if response.status_code == 302 else 'No redirect'}")
            
            # Print call counts
            print(f"mock_add.call_count: {mock_add.call_count}")
            print(f"mock_commit.call_count: {mock_commit.call_count}")
            print(f"mock_hash.call_count: {mock_hash.call_count}")
            
            if mock_add.call_args:
                print(f"mock_add call args: {mock_add.call_args}")
            
            # Verify the password was hashed
            mock_hash.assert_called_once_with(test_user_data['password'], method='pbkdf2:sha256')
            
            # Verify database operations
            assert mock_add.called
            assert mock_commit.called
            
            # Should redirect to login page after successful registration
            assert response.status_code == 302
            assert '/auth/login' in response.location

def test_login_form(client, test_user_data):
    data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post('/auth/login', data=data)
    assert response.status_code in [200, 302]  # Either renders form again or redirects 