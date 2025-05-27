import pytest
from flask import url_for
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token

def test_index_route_without_user(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Level Up Your Fitness' in response.data
    assert b'Gamify Your Fitness Journey' in response.data
    assert b'Start Your Journey' in response.data

def test_index_route_with_user(client, app):
    mock_user = MagicMock(
        id=1,
        username="testuser",
        exercise_points=0,
        get_rank=lambda: "Bronze"
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('flask_jwt_extended.get_jwt_identity', return_value=mock_user.id), \
             patch('extensions.db.session.get', return_value=mock_user):
            
            # Set the JWT token in the cookie
            client.set_cookie('access_token_cookie', access_token)
            
            response = client.get('/')
            assert response.status_code == 302  # Expect redirect
            assert '/dashboard' in response.location  # Should redirect to dashboard

def test_static_serve(client):
    response = client.get('/static/css/style.css')
    assert response.status_code == 200
    assert b'css' in response.data.lower() 