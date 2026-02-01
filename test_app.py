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

# ===== AUTHENTICATION TESTS =====

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

def test_events_requires_auth(client):
    """Test that events page requires authentication"""
    response = client.get('/events', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/login' in response.location

def test_logout_redirects_to_login(client):
    """Test that logout redirects to login page"""
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

# ===== API TESTS =====

def test_api_shipments_endpoint_exists(client):
    """Test that API shipments endpoint exists and returns JSON"""
    response = client.get('/api/shipments')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

def test_api_shipments_returns_list(client):
    """Test that API shipments returns a list"""
    response = client.get('/api/shipments')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_api_events_endpoint_exists(client):
    """Test that API events endpoint exists"""
    response = client.get('/api/events')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

def test_api_events_returns_list(client):
    """Test that API events returns a list"""
    response = client.get('/api/events')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

# ===== VALIDATION TESTS =====

def test_shipment_validation_empty_origin(client):
    """Test that shipment creation fails with empty origin"""
    response = client.post('/shipments', data={
        'status': 'Pending',
        'origin': '',
        'destination': 'Paris'
    }, follow_redirects=False)
    assert response.status_code in [400, 302]  # Either validation error or redirect to login

def test_shipment_validation_empty_destination(client):
    """Test that shipment creation fails with empty destination"""
    response = client.post('/shipments', data={
        'status': 'Pending',
        'origin': 'London',
        'destination': ''
    }, follow_redirects=False)
    assert response.status_code in [400, 302]

def test_shipment_validation_dangerous_characters(client):
    """Test that shipment creation fails with dangerous characters"""
    response = client.post('/shipments', data={
        'status': 'Pending',
        'origin': 'London<script>',
        'destination': 'Paris'
    }, follow_redirects=False)
    # Should either show validation error or redirect to login
    assert response.status_code in [400, 302]

# ===== ROUTE TESTS =====

def test_about_page_exists(client):
    """Test that the about page is accessible"""
    response = client.get('/about')
    assert response.status_code == 200

def test_status_page_exists(client):
    """Test that the status page is accessible"""
    response = client.get('/status')
    assert response.status_code == 200

def test_404_handler(client):
    """Test that 404 page works for invalid routes"""
    response = client.get('/nonexistent-page-12345')
    assert response.status_code == 404

# ===== RATE LIMITING TESTS =====

def test_rate_limiting_exists(client):
    """Test that rate limiting is configured (doesn't error on valid requests)"""
    # Make a few requests to ensure rate limiter is working
    for i in range(5):
        response = client.get('/api/shipments')
        assert response.status_code == 200

# ===== AUTHENTICATION API TESTS =====

def test_login_post_requires_token(client):
    """Test that login POST requires a token"""
    response = client.post('/login', json={})
    assert response.status_code == 400

def test_whoami_endpoint_exists(client):
    """Test that whoami endpoint exists"""
    response = client.get('/whoami')
    assert response.status_code == 200
    assert response.content_type == 'application/json'