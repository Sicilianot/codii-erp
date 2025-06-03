from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine # Asegurarse de importar create_engine
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Importar nuestra aplicación Flask y la instancia db
import sys
import os

sys.path.append(os.getcwd())

# Importar la función create_app y la instancia db de Flask-SQLAlchemy
from app import create_app, db

# Importar explícitamente todos los modelos para que Alembic los detecte
# Esto es necesario cuando se usa create_app y los modelos no están en el mismo archivo
from models.user import User
from models.material import Material
from models.supplier import Supplier
# from models.customer import Customer # No existe
# from models.employee import Employee # No existe
from models.purchase_order import PurchaseOrder
# from models.sales_order import SalesOrder # No existe
# from models.invoice import Invoice # No existe
# from models.inventory import Inventory # No existe
from models.production_order import ProductionOrder, ProductionOrderItem
from models.maintenance_work_order import MaintenanceWorkOrder # Nombre corregido
from models.material_category import MaterialCategory
from models.material_movement import MaterialMovement
from models.product import Product, ProductComponent
from models.product_category import ProductCategory
from models.quality_audit import QualityAudit
from models.quality_audit_finding import QualityAuditFinding
from models.quality_certificate import QualityCertificate
from models.quality_document import QualityDocument
from models.quality_inspection import QualityInspection, QualityCheckpoint
from models.quality_non_conformity import QualityNonConformity
from models.capa import CAPA
# TODO: Añadir importaciones para otros modelos si se crean los archivos (Equipment, QualityStandard, etc.)

# Llamar a create_app para obtener la instancia de la aplicación
# Puedes pasar una configuración específica si la tienes (ej. para testing)
app = create_app() 

# Establecer la metadata de nuestros modelos
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Configurar la URL de la base de datos para Alembic
# Leer de la configuración de la aplicación Flask, que a su vez lee de variables de entorno
def get_url():
    # Usamos la URI de la base de datos configurada en nuestra aplicación Flask
    # Esto asegura que Alembic use la misma base de datos que la aplicación
    return app.config['SQLALCHEMY_DATABASE_URI']


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # url = config.get_main_option("sqlalchemy.url") # Comentar o eliminar esta línea
    url = get_url() # Usar nuestra función para obtener la URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # ) # Comentar o eliminar esta sección

    # Usar nuestra función para obtener la URL y crear el motor directamente
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
