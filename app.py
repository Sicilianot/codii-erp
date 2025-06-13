import os
import logging
from logging.handlers import StreamHandler
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
from whitenoise import WhiteNoise

from config import Config, DevelopmentConfig, TestingConfig

# Inicializar extensiones fuera de create_app para que puedan ser importadas
# y utilizadas por otras partes de la aplicación y por Alembic.
# Se inicializan SIn la app y luego se asocian a la app dentro de create_app.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Definir la función de carga de usuario para Flask-Login
@login_manager.user_loader

def create_app(config_class=None):
    # Cargar variables de entorno desde un archivo .env (solo para desarrollo)
    load_dotenv()

    # Inicializar la aplicación Flask
    # Ensure static_folder points to 'app/static' and served from '/static'
    app = Flask(__name__, static_folder='app/static', static_url_path='/static')

    # Configuración de la aplicación
    # Si se proporciona una clase de configuración, úsala
    if config_class:
        app.config.from_object(config_class)
    else:
        # Determinar la configuración basada en FLASK_ENV o usar Config por defecto (producción)
        flask_env = os.environ.get('FLASK_ENV')
        if flask_env == 'development':
            app.config.from_object(DevelopmentConfig)
        elif flask_env == 'testing': # Though tests will usually pass TestingConfig directly
            app.config.from_object(TestingConfig)
        else:
            app.config.from_object(Config) # Default to base Config (production-like)

    # Configuración de logging para producción
    # Esta lógica se mantiene, pero DEBUG y TESTING ahora vienen de la clase de configuración.
    if not app.debug and not app.testing:
        if not app.logger.handlers:
            stream_handler = StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('MicroERP startup')

    # Inicializar extensiones asociándolas a la aplicación
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importar y registrar Blueprints
    from routes.mm import mm
    from routes.pp import pp
    from routes.qm import qm
    # TODO: Implement and register user blueprint (routes/user.py does not exist yet), and other blueprints (etc.)
    from routes.auth import auth

    app.register_blueprint(mm)
    app.register_blueprint(pp)
    app.register_blueprint(qm)
    app.register_blueprint(auth)

    # Registrar manejadores de errores
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        # En caso de un error 500, es bueno hacer un rollback de la sesión de DB
        # por si el error fue causado por un problema en la DB.
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Integrar WhiteNoise para servir archivos estáticos en producción
    # Debe hacerse después de que toda la configuración de la app y blueprints estén listos,
    # pero antes de retornar la app.
    # WhiteNoise utilizará app.static_folder y app.static_url_path definidos en Flask()
    # No aplicar WhiteNoise durante las pruebas por defecto para no interferir con el test client.
    # TestingConfig ya tiene TESTING = True.
    if not app.config.get('TESTING'):
        if not app.config.get('DEBUG'): # Solo aplicar en modo no-debug (producción)
            app.wsgi_app = WhiteNoise(app.wsgi_app, root=app.static_folder, prefix=app.static_url_path)
        else:
            # En modo debug, Flask sirve los estáticos bien. WhiteNoise es para producción.
            app.logger.info('WhiteNoise is disabled in DEBUG mode.')
    else:
        app.logger.info('WhiteNoise is disabled in TESTING mode.')


    return app

# Si este archivo se ejecuta directamente, crear y ejecutar la aplicación
if __name__ == '__main__':
    # Al ejecutar directamente, usar DevelopmentConfig
    # La variable de entorno FLASK_DEBUG=1 o app.run(debug=True) anulará config.DEBUG si es necesario.
    app = create_app(DevelopmentConfig)
    # app.run() ya no necesita debug=True aquí si DevelopmentConfig.DEBUG es True.
    # Si quieres forzar debug True independientemente de la config, puedes dejar app.run(debug=True)
    app.run()