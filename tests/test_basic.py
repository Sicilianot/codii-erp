import pytest
from flask import url_for

def test_app_exists(app):
    """Test if the Flask app instance exists."""
    assert app is not None

def test_app_is_testing(app):
    """Test if the app is configured for testing."""
    assert app.config['TESTING'] is True
    assert app.config['DEBUG'] is True # As per TestingConfig
    assert "sqlite:///:memory:" in app.config['SQLALCHEMY_DATABASE_URI']
    assert app.config['WTF_CSRF_ENABLED'] is False

def test_home_page_redirects_to_login(client):
    """Test that the home page '/' redirects to the login page."""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    # Check if the request was redirected to the login page
    # This assumes your login route is 'auth.login'
    # and the content of login page has "Sign In" or similar text.
    assert b"Sign In" in response.data  # Adjust if your login page content is different
    # Or check the path after redirect
    assert url_for('auth.login', _external=False) in response.request.path


def test_login_page_loads(client):
    """Test that the /auth/login page loads successfully."""
    # Assuming 'auth.login' is the route name for your login page
    # If you have a blueprint 'auth', url_for should be 'auth.login'
    try:
        login_url = url_for('auth.login')
    except Exception as e:
        # Fallback if url_for fails (e.g. context not fully available in simple test)
        login_url = '/auth/login'

    response = client.get(login_url)
    assert response.status_code == 200
    assert b"Sign In" in response.data # Or other text unique to your login page

def test_non_existent_page_returns_404(client):
    """Test that a non-existent page returns a 404 error."""
    response = client.get('/this-page-does-not-exist')
    assert response.status_code == 404
    # Check if it uses the custom 404 page
    assert b"Page Not Found" in response.data
    assert b"Sorry, the page you are looking for does not exist." in response.data

def test_create_app_no_config_default(app_context):
    """
    Test if create_app uses default Config when no FLASK_ENV is set.
    This requires app_context if create_app itself needs it.
    However, create_app doesn't use app_context directly, so we can call it.
    We need to temporarily unset FLASK_ENV for this test.
    """
    import os
    from app import create_app
    from config import Config, DevelopmentConfig

    original_flask_env = os.environ.get('FLASK_ENV')
    if original_flask_env:
        del os.environ['FLASK_ENV']

    temp_app = create_app() # No config_class, FLASK_ENV not set

    if original_flask_env: # Restore it
        os.environ['FLASK_ENV'] = original_flask_env

    assert temp_app.config['DEBUG'] == Config.DEBUG # Should be False from base Config
    assert temp_app.config['SECRET_KEY'] == Config.SECRET_KEY


@pytest.fixture
def app_context(app):
    """Provides an application context for tests that need it."""
    with app.app_context():
        yield
