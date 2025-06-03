import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

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
    app = Flask(__name__)

    # Configuración de la aplicación
    # Si se proporciona una clase de configuración, úsala
    if config_class:
        app.config.from_object(config_class)
    else:
        # Utilizar variables de entorno para la configuración sensible
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_muy_secreta_y_dificil_de_adivinar_por_defecto') # Usar variable de entorno o valor por defecto en desarrollo
        # Usar la variable de entorno DATABASE_URL para la URI de la base de datos
        # Ejemplo para PostgreSQL: postgresql://user:password@host:port/database
        # Usar un valor por defecto para desarrollo si no se especifica
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tmp/site.db') # Usar SQLite por defecto en desarrollo
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desactiva el seguimiento de modificaciones innecesarias
        # TODO: Añadir más configuración aquí si es necesario (e.g., UPLOAD_FOLDER)
        app.config['UPLOAD_FOLDER'] = 'uploads'
        # Desactivar el modo debug para producción si no se usa una clase de configuración específica
        app.config['DEBUG'] = False

    # Inicializar extensiones asociándolas a la aplicación
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Importar y registrar Blueprints
    from routes.mm import mm
    from routes.pp import pp
    from routes.qm import qm
    # TODO: Importar y registrar otros Blueprints (auth, user, etc.)
    from routes.auth import auth

    app.register_blueprint(mm)
    app.register_blueprint(pp)
    app.register_blueprint(qm)
    app.register_blueprint(auth)

    return app

# Si este archivo se ejecuta directamente, crear y ejecutar la aplicación
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 