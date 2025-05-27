import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

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

def test_dashboard_with_auth(client):
    with patch('utils.helpers.get_current_user', return_value={'id': 1, 'exercise_points': 0}):
        response = client.get('/dashboard/')
        assert response.status_code == 200

def test_exercise_submission(client):
    mock_user = MagicMock(id=1, exercise_points=0)
    with patch('utils.helpers.get_current_user', return_value=mock_user):
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
        response = client.post('/dashboard/', data=data)
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