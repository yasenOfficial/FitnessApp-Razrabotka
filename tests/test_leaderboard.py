import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token

def test_leaderboard_unauthorized(client):
    response = client.get('/leaderboard/')
    assert response.status_code in [302, 401]  # Either redirect to login or unauthorized

def test_leaderboard_with_auth(client, app):
    mock_user = MagicMock(id=1, username="testuser", exercise_points=100)
    mock_top_players = [
        MagicMock(id=2, username="user1", exercise_points=500),
        MagicMock(id=3, username="user2", exercise_points=400),
        MagicMock(id=1, username="testuser", exercise_points=100)
    ]
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_current_user', return_value=mock_user), \
             patch('models.User.query') as mock_query, \
             patch('extensions.db.session.get', return_value=mock_user):
            
            mock_query.order_by().limit().all.return_value = mock_top_players
            mock_query.order_by().all.return_value = mock_top_players
            
            # Make request with token in cookie
            client.set_cookie('access_token_cookie', access_token)
            response = client.get('/leaderboard/')
            assert response.status_code == 200
            assert b'user1' in response.data
            assert b'user2' in response.data
            assert b'testuser' in response.data

def test_leaderboard_user_rank(client, app):
    mock_user = MagicMock(id=1, username="testuser", exercise_points=100)
    mock_all_users = [
        MagicMock(id=2, username="user1", exercise_points=500),
        MagicMock(id=3, username="user2", exercise_points=400),
        MagicMock(id=1, username="testuser", exercise_points=100)
    ]
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_current_user', return_value=mock_user), \
             patch('models.User.query') as mock_query, \
             patch('extensions.db.session.get', return_value=mock_user):
            
            mock_query.order_by().limit().all.return_value = mock_all_users[:2]  # Top 2 players
            mock_query.order_by().all.return_value = mock_all_users  # All users for rank calculation
            
            # Make request with token in cookie
            client.set_cookie('access_token_cookie', access_token)
            response = client.get('/leaderboard/')
            assert response.status_code == 200
            # User should be rank 3
            assert b'3' in response.data

def test_leaderboard_empty(client, app):
    # Create a proper mock user object with all required attributes
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com",
        exercise_points=0,
        achievements=[],
        get_rank=lambda: "Bronze",  # Add get_rank method
        calculate_achievements=lambda: None  # Add calculate_achievements method
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_current_user', return_value=mock_user), \
             patch('models.User.query') as mock_query, \
             patch('extensions.db.session.get', return_value=mock_user):
            
            # Mock empty leaderboard
            mock_query.order_by().limit().all.return_value = []
            mock_query.order_by().all.return_value = [mock_user]  # For rank calculation
            
            # Make request with token in cookie
            client.set_cookie('access_token_cookie', access_token)
            response = client.get('/leaderboard/')
            
            # Verify response
            assert response.status_code == 200
            assert b'No players found' in response.data  # Check empty leaderboard message
            assert b'Your Stats' in response.data  # Check stats section exists
            assert b'Total Points' in response.data  # Check points are shown
            assert b'Your Position' in response.data  # Check rank is shown 