import pytest
from flask import url_for
import json
from unittest.mock import patch, MagicMock
from models import User
from extensions import db

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

def test_register_api(client, app):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    }

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
                                data=json.dumps(data),
                                content_type='application/json')
            
            assert response.status_code == 200
            assert mock_add.called  # Verify user was added to db
            assert mock_commit.called  # Verify changes were committed
            assert mock_send.called  # Verify confirmation email was sent
            
            response_data = json.loads(response.data)
            assert response_data['success'] == True
            assert 'Registered!' in response_data['message']

def test_login_api(client):
    data = {
        "username": "testuser",
        "password": "TestPass123"
    }
    response = client.post('/auth/api/login',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code in [200, 401, 403]  # Success or invalid credentials or email not confirmed

def test_logout(client):
    response = client.post('/auth/api/logout')
    assert response.status_code == 200
    assert json.loads(response.data)['success'] == True

def test_register_form(client):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    }
    response = client.post('/auth/register', data=data)
    assert response.status_code in [200, 302]  # Either renders form again or redirects

def test_login_form(client):
    data = {
        "username": "testuser",
        "password": "TestPass123"
    }
    response = client.post('/auth/login', data=data)
    assert response.status_code in [200, 302]  # Either renders form again or redirects 