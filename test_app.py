import pytest
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page_exists(client):
    """Test that the login page is accessible"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data

def test_dashboard_requires_auth(client):
    """Test that dashboard redirects to login when not authenticated"""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/login' in response.location

def test_shipments_requires_auth(client):
    """Test that shipments page requires authentication"""
    response = client.get('/shipments', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/login' in response.location

def test_api_shipments_endpoint_exists(client):
    """Test that API shipments endpoint exists"""
    response = client.get('/api/shipments')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

def test_geocode_requires_auth(client):
    """Test that geocode page requires authentication"""
    response = client.get('/geocode', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/login' in response.location

def test_distance_requires_auth(client):
    """Test that distance page requires authentication"""
    response = client.get('/distance', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/login' in response.location

def test_about_page_exists(client):
    """Test that the about page is accessible"""
    response = client.get('/about')
    assert response.status_code == 200

def test_404_handler(client):
    """Test that 404 page works for invalid routes"""
    response = client.get('/nonexistent-page-12345')
    assert response.status_code == 404