import pytest
from unittest.mock import patch, MagicMock

def test_leaderboard_unauthorized(client):
    response = client.get('/leaderboard/')
    assert response.status_code in [302, 401]  # Either redirect to login or unauthorized

def test_leaderboard_with_auth(client):
    mock_user = MagicMock(id=1, username="testuser", exercise_points=100)
    mock_top_players = [
        MagicMock(id=2, username="user1", exercise_points=500),
        MagicMock(id=3, username="user2", exercise_points=400),
        MagicMock(id=1, username="testuser", exercise_points=100)
    ]
    
    with patch('utils.helpers.get_current_user', return_value=mock_user), \
         patch('models.User.query') as mock_query:
        
        mock_query.order_by().limit().all.return_value = mock_top_players
        mock_query.order_by().all.return_value = mock_top_players
        
        response = client.get('/leaderboard/')
        assert response.status_code == 200
        assert b'user1' in response.data
        assert b'user2' in response.data
        assert b'testuser' in response.data

def test_leaderboard_user_rank(client):
    mock_user = MagicMock(id=1, username="testuser", exercise_points=100)
    mock_all_users = [
        MagicMock(id=2, username="user1", exercise_points=500),
        MagicMock(id=3, username="user2", exercise_points=400),
        MagicMock(id=1, username="testuser", exercise_points=100)
    ]
    
    with patch('utils.helpers.get_current_user', return_value=mock_user), \
         patch('models.User.query') as mock_query:
        
        mock_query.order_by().limit().all.return_value = mock_all_users[:2]  # Top 2 players
        mock_query.order_by().all.return_value = mock_all_users  # All users for rank calculation
        
        response = client.get('/leaderboard/')
        assert response.status_code == 200
        # User should be rank 3
        assert b'3' in response.data

def test_leaderboard_empty(client):
    mock_user = MagicMock(id=1, username="testuser", exercise_points=0)
    
    with patch('utils.helpers.get_current_user', return_value=mock_user), \
         patch('models.User.query') as mock_query:
        
        mock_query.order_by().limit().all.return_value = []
        mock_query.order_by().all.return_value = [mock_user]
        
        response = client.get('/leaderboard/')
        assert response.status_code == 200
        # Should still show the current user
        assert b'testuser' in response.data 