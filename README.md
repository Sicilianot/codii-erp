# Sistema ERP Modular

Un sistema ERP (Enterprise Resource Planning) modular desarrollado con Python, Flask y SQLAlchemy.

## Características

- Sistema modular inspirado en SAP
- Autenticación de usuarios y gestión de roles
- Interfaz moderna con Tailwind CSS
- Base de datos PostgreSQL (SQLite para desarrollo)
- API RESTful para integración con otros sistemas

## Módulos

Actualmente implementados:
- **Auth** (Autenticación y Gestión de Usuarios) - Funcionalidad central para el acceso.
- **MM (Gestión de Materiales)** - Incluye gestión de proveedores, categorías de materiales, materiales, órdenes de compra, inventario y movimientos.
- **PP (Planificación de Producción)** - Incluye gestión de categorías de productos, productos y órdenes de producción.
- **QM (Gestión de Calidad)** - Incluye gestión de documentos, auditorías, no conformidades, CAPAs, inspecciones y certificados.

Planeados (aún no implementados):
- SD (Ventas y Distribución)
- FI (Finanzas)
- CO (Controlling)
- HCM (Gestión de Recursos Humanos)
- WM (Gestión de Almacenes)
- PM (Mantenimiento de Planta)
- BI (Business Intelligence)

## Requisitos

- Python 3.11+
- PostgreSQL (opcional, SQLite por defecto)
- pip

## Instalación

1. Clonar el repositorio:
```bash
git clone [url-del-repositorio]
cd erp-system
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. Inicializar la base de datos:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Ejecutar la aplicación:

   Para desarrollo:
   ```bash
   flask run
   ```
   Asegúrate de tener `FLASK_ENV=development` o `FLASK_DEBUG=1` configurado en tu archivo `.env` para activar el modo de depuración y otras características de desarrollo.

   Para producción (ejemplo usando Gunicorn, similar al `Procfile`):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:$PORT 'app:create_app()'
   ```
   En un entorno de producción, deberás configurar variables de entorno como `PORT` (generalmente provista por la plataforma de hosting), `DATABASE_URL` (para PostgreSQL), `SECRET_KEY`, y `FLASK_ENV=production` (o asegúrate de que `DEBUG` sea `False` en la configuración).

## Estructura del Proyecto

```
erp-system/
├── app.py
├── requirements.txt
├── .env
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── ...
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   └── ...
├── templates/
│   ├── base.html
│   ├── auth/
│   └── ...
└── static/
    ├── css/
    └── js/
```

## Testing

Para ejecutar la suite de pruebas, asegúrate de tener `pytest` instalado (incluido en `requirements.txt`). Desde la raíz del proyecto, ejecuta:

```bash
python -m pytest
```

o simplemente:

```bash
pytest
```

Las pruebas están ubicadas en el directorio `tests/`. La configuración de las pruebas utiliza una base de datos SQLite en memoria para no interferir con los datos de desarrollo.

## Guía de Usuario

Para una guía sobre cómo utilizar la interfaz y las funcionalidades de la aplicación, consulta la [Guía de Usuario Frontend](USER_GUIDE.md).

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 