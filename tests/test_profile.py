import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token

def test_profile_unauthorized(client):
    response = client.get('/profile/')
    assert response.status_code in [302, 401]  # Either redirect to login or unauthorized

def test_profile_with_auth(client, app):
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com"
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_jwt_identity', return_value=mock_user.id), \
             patch('extensions.db.session.get', return_value=mock_user):
            
            # Set the JWT token in the cookie
            client.set_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], access_token)
            
            response = client.get('/profile/')
            assert response.status_code == 200
            assert b'testuser' in response.data
            assert b'test@example.com' in response.data

def test_edit_profile_get(client, app):
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com"
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_jwt_identity', return_value=mock_user.id), \
             patch('extensions.db.session.get', return_value=mock_user):
            
            # Set the JWT token in the cookie
            client.set_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], access_token)
            
            response = client.get('/profile/edit')
            assert response.status_code == 200
            assert b'testuser' in response.data
            assert b'test@example.com' in response.data

def test_edit_profile_post_success(client, app):
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com",
        set_password=lambda x: None
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_jwt_identity', return_value=mock_user.id), \
             patch('extensions.db.session.get', return_value=mock_user), \
             patch('models.User.query') as mock_query:
            
            # Mock the username/email check to return None (meaning no existing user)
            mock_query.filter_by().first.return_value = None
            
            # Set the JWT token in the cookie
            client.set_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], access_token)
            
            data = {
                'username': 'newusername',
                'email': 'newemail@example.com',
                'password': 'newpassword123'
            }
            
            response = client.post('/profile/edit', data=data)
            assert response.status_code == 302  # Should redirect to profile page
            assert response.location == '/profile'

def test_edit_profile_post_empty_fields(client, app):
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com"
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_jwt_identity', return_value=mock_user.id), \
             patch('extensions.db.session.get', return_value=mock_user):
            
            # Set the JWT token in the cookie
            client.set_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], access_token)
            
            data = {
                'username': '',
                'email': '',
                'password': 'newpassword123'
            }
            
            response = client.post('/profile/edit', data=data)
            assert response.status_code == 200
            assert b'cannot be empty' in response.data

def test_edit_profile_username_taken(client, app):
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com"
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_jwt_identity', return_value=mock_user.id), \
             patch('extensions.db.session.get', return_value=mock_user), \
             patch('models.User.query') as mock_query:
            
            # Mock that username is already taken
            mock_query.filter_by().first.return_value = MagicMock()
            
            # Set the JWT token in the cookie
            client.set_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], access_token)
            
            data = {
                'username': 'takenusername',
                'email': 'newemail@example.com',
                'password': 'newpassword123'
            }
            
            response = client.post('/profile/edit', data=data)
            assert response.status_code == 200
            assert b'Username already taken' in response.data 