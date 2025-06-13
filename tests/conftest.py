import pytest
from app import create_app, db
from config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app(TestingConfig)
    return app

@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='session')
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture(scope='function') # Use function scope for db to ensure clean db for each test
def init_database(app):
    """Create the database and the database table """
    with app.app_context():
        db.create_all()
        yield db # provide the fixture value
        db.session.remove()
        db.drop_all()

# Optional: If you have user models and want to create a test user
# from app.models.user import User # Adjust import path as needed
# @pytest.fixture(scope='function')
# def test_user(init_database):
#     user = User(username='testuser', email='test@example.com')
#     user.set_password('password123')
#     db.session.add(user)
#     db.session.commit()
#     return user
