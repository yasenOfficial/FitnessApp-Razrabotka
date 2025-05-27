import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from flask_jwt_extended import create_access_token
from utils.helpers import get_current_user

def test_achievements_unauthorized(client):
    response = client.get('/achievements/')
    assert response.status_code in [302, 401]  # Either redirect to login or unauthorized

def test_achievements_with_auth(client, app):
    mock_user = MagicMock(
        id=1,
        exercise_points=250,
        achievements=[],
        calculate_achievements=lambda: None
    )
    
    with app.app_context():
        access_token = create_access_token(identity=1)
        client.set_cookie('access_token_cookie', access_token)
        
        with patch('routes.achievements.get_current_user', return_value=mock_user) as mock_get_user:
            response = client.get('/achievements/')
            assert response.status_code == 200
            # Check for content that exists in the template
            assert b'Achievements' in response.data
            assert b'Complete challenges' in response.data
            assert b'250' in response.data  # exercise points

def test_achievements_progress_calculation(client, app):
    # Test with points between Beginner and Intermediate
    mock_user = MagicMock(
        id=1,
        exercise_points=300,
        achievements=[],
        calculate_achievements=lambda: None
    )
    
    with app.app_context():
        access_token = create_access_token(identity=1)
        client.set_cookie('access_token_cookie', access_token)
        
        with patch('routes.achievements.get_current_user', return_value=mock_user) as mock_get_user:
            response = client.get('/achievements/')
            assert response.status_code == 200
            assert b'300' in response.data  # exercise points
            assert b'Current Points' in response.data

def test_achievements_master_tier(client, app):
    # Test with points above Master tier
    mock_user = MagicMock(
        id=1,
        exercise_points=15000,
        achievements=[],
        calculate_achievements=lambda: None
    )
    
    with app.app_context():
        access_token = create_access_token(identity=1)
        client.set_cookie('access_token_cookie', access_token)
        
        with patch('routes.achievements.get_current_user', return_value=mock_user) as mock_get_user:
            response = client.get('/achievements/')
            assert response.status_code == 200
            assert b'15000' in response.data  # exercise points
            assert b'Maximum tier achieved!' in response.data

def test_achievements_unlocked_status(client, app):
    # Test achievement unlocking logic
    mock_user = MagicMock(
        id=1,
        exercise_points=150,
        achievements=[],
        calculate_achievements=lambda: None
    )
    
    with app.app_context():
        access_token = create_access_token(identity=1)
        client.set_cookie('access_token_cookie', access_token)
        
        with patch('routes.achievements.get_current_user', return_value=mock_user) as mock_get_user:
            response = client.get('/achievements/')
            assert response.status_code == 200
            # With 150 points, "First Steps" (10 points) and "Warming Up" (50 points) should be unlocked
            assert b'First Steps' in response.data
            assert b'Warming Up' in response.data
            # Check that the achievements are not marked as locked
            assert b'locked">First Steps' not in response.data 