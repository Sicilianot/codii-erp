import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'una_clave_muy_secreta_y_dificil_de_adivinar_por_defecto')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tmp/site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    DEBUG = False # Base config should be for production

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL', 'sqlite:///tmp/dev_site.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:') # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF forms for testing ease
    DEBUG = True # Often helpful for tests, though not strictly necessary if TESTING is True

# You might want to add a ProductionConfig explicitly
# class ProductionConfig(Config):
#     # Production specific settings, e.g. stricter logging, different DB URI from env
#     pass
