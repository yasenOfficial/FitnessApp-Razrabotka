import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
from flask_jwt_extended import create_access_token

def test_dashboard_unauthorized(client):
    response = client.get('/dashboard/')
    assert response.status_code in [302, 401]  # Either redirect to login or unauthorized

@pytest.mark.parametrize("exercise_type", ["pushup", "situp", "squat", "pullup", "burpee", "plank", "run"])
def test_exercise_stats_endpoint(client, exercise_type):
    with patch('utils.helpers.get_current_user', return_value={'id': 1}):
        response = client.get(f'/dashboard/api/exercise-stats/{exercise_type}')
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'dates' in data
            assert 'counts' in data

def test_dashboard_with_auth(client, app):
    # Create a proper mock user object with all required attributes
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com",
        exercise_points=0,
        achievements=[],
        calculate_achievements=lambda: None
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_current_user', return_value=mock_user), \
             patch('models.User.query') as mock_query, \
             patch('extensions.db.session.query') as mock_db_query, \
             patch('extensions.db.session.get', return_value=mock_user):
            
            # Mock the database query for exercise ranks
            mock_sum = MagicMock()
            mock_sum.scalar.return_value = 0
            mock_db_query.return_value.filter_by.return_value.scalar.return_value = 0
            
            # Make request with token in cookie
            client.set_cookie('access_token_cookie', access_token)
            response = client.get('/dashboard/')
            assert response.status_code == 200

def test_exercise_submission(client, app):
    # Create a proper mock user object with all required attributes
    mock_user = MagicMock(
        id=1,
        username="testuser",
        email="test@example.com",
        exercise_points=0,
        achievements=[],
        calculate_achievements=lambda: None
    )
    
    with app.app_context():
        # Create a valid access token
        access_token = create_access_token(identity=mock_user.id)
        
        with patch('utils.helpers.get_current_user', return_value=mock_user), \
             patch('models.User.query') as mock_query, \
             patch('extensions.db.session.query') as mock_db_query, \
             patch('extensions.db.session.get', return_value=mock_user), \
             patch('extensions.db.session.add') as mock_add, \
             patch('extensions.db.session.commit') as mock_commit:
            
            # Mock the database query for exercise ranks
            mock_db_query.return_value.filter_by.return_value.scalar.return_value = 0
            
            data = {
                'pushup': '10',
                'pushup_date': datetime.now().strftime('%Y-%m-%d'),
                'situp': '0',
                'squat': '0',
                'pullup': '0',
                'burpee': '0',
                'plank': '0',
                'run': '0'
            }
            
            # Make request with token in cookie
            client.set_cookie('access_token_cookie', access_token)
            response = client.post('/dashboard/', data=data)
            
            # Verify database operations
            assert mock_add.called
            assert mock_commit.called
            assert response.status_code in [200, 302]  # Either success or redirect

def test_get_daily_routine():
    from routes.dashboard import get_daily_routine
    routine = get_daily_routine()
    assert isinstance(routine, list)
    assert len(routine) == 7
    assert all(isinstance(ex, dict) for ex in routine)

def test_get_exercise_multipliers():
    from routes.dashboard import get_exercise_multipliers
    multipliers = get_exercise_multipliers()
    assert isinstance(multipliers, dict)
    assert len(multipliers) == 7
    assert all(isinstance(v, float) for v in multipliers.values())

def test_validate_exercise_date():
    from routes.dashboard import validate_exercise_date
    today = datetime.now().date()
    
    # Test valid date
    date_str = today.strftime('%Y-%m-%d')
    result, error = validate_exercise_date(date_str, today)
    assert error is None
    assert result == today

    # Test future date
    future_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    result, error = validate_exercise_date(future_date, today)
    assert error is not None
    assert result is None 