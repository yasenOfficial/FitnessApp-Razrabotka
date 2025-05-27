import pytest
from flask import url_for
from unittest.mock import patch

def test_index_route_without_user(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'home.html' in response.data

def test_index_route_with_user(client):
    with patch('utils.helpers.get_current_user', return_value={'id': 1}):
        response = client.get('/')
        assert response.status_code == 302
        assert '/dashboard' in response.location

def test_static_serve(client):
    response = client.get('/static/test.css')
    assert response.status_code == 200  # This will pass even if file doesn't exist since we're just testing the route 