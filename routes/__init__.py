from flask import Blueprint

# Crear blueprints para cada módulo
auth = Blueprint('auth', __name__)
mm = Blueprint('mm', __name__)
sd = Blueprint('sd', __name__)
fi = Blueprint('fi', __name__)
co = Blueprint('co', __name__)
hcm = Blueprint('hcm', __name__)
pp = Blueprint('pp', __name__)
wm = Blueprint('wm', __name__)
qm = Blueprint('qm', __name__)
pm = Blueprint('pm', __name__)
bi = Blueprint('bi', __name__)

# Importar rutas de cada módulo
from .auth import *
from .mm import *
from .sd import *
from .fi import *
from .co import *
from .hcm import *
from .pp import *
from .wm import *
from .qm import *
from .pm import *
from .bi import * 