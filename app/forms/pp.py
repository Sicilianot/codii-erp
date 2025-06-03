from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, DateTimeField, IntegerField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from datetime import datetime
from models import Product, Material, ProductCategory, ProductComponent, ProductProcess, ProductionOrder, QualityCheck, User # Actualizada la importación, añadir User
from wtforms_sqlalchemy.fields import QuerySelectField

def get_materials_for_pp(): # Define a query factory for materials
    # Import Material from the correct path (now models/material.py via models/__init__.py)
    return Material.query.all()

def get_users_for_pp(): # Nueva query factory para usuarios
    # Import User from the correct path (now models/user.py via models/__init__.py)
    # Podríamos filtrar por roles si solo ciertos usuarios pueden ser operadores
    return User.query.order_by(User.username).all()

class ProductForm(FlaskForm):
    id = HiddenField()
    code = StringField('Código', validators=[DataRequired(), Length(max=20)])
    name = StringField('Nombre del Producto', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional()])
    product_type = StringField('Tipo de Producto', validators=[DataRequired(), Length(max=50)]) # Tanque, intercambiador, etc.
    material_type = StringField('Tipo de Material Principal', validators=[DataRequired(), Length(max=50)]) # AISI304, etc.
    unit_of_measure = StringField('Unidad de Medida', validators=[DataRequired(), Length(max=20)]) # unidad, kg, etc.
    standard_price = FloatField('Precio Estándar', validators=[Optional(), NumberRange(min=0)])
    estimated_production_time = FloatField('Tiempo Estimado de Producción (horas)', validators=[Optional(), NumberRange(min=0)])
    weight = FloatField('Peso (kg)', validators=[Optional(), NumberRange(min=0)])
    dimensions = StringField('Dimensiones (LxWxH)', validators=[Optional(), Length(max=50)])
    # technical_specs = db.Column(db.JSON) # JSONField requires a different approach, handle later if needed
    # welding_specs = db.Column(db.JSON) # JSONField requires a different approach, handle later if needed
    is_active = BooleanField('Activo')
    submit = SubmitField('Guardar Producto')

class ProductCategoryForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    name = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=500)
    ])
    color = StringField('Color', validators=[
        DataRequired(),
        Length(min=7, max=7)
    ])
    is_active = BooleanField('Activo')

class ProductComponentForm(FlaskForm):
    id = HiddenField() # Para edición
    # Use QuerySelectField to select a Material
    material = QuerySelectField('Material', query_factory=get_materials_for_pp, allow_blank=False, get_label='name', validators=[DataRequired()])
    quantity = FloatField('Cantidad', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    unit_of_measure = StringField('Unidad de Medida', validators=[
        DataRequired(),
        Length(max=20)
    ])
    weight = FloatField('Peso (kg)', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    position = StringField('Posición', validators=[
        Optional(),
        Length(max=50)
    ])
    notes = TextAreaField('Notas', validators=[
        Optional(),
        Length(max=500)
    ])
    submit = SubmitField('Guardar Componente')

class ProductProcessForm(FlaskForm):
    id = HiddenField() # Para edición
    process_type = StringField('Tipo de Proceso', validators=[
        DataRequired(),
        Length(max=50)
    ])
    sequence = IntegerField('Secuencia', validators=[
        DataRequired(),
        NumberRange(min=1)
    ])
    estimated_time = FloatField('Tiempo Estimado (horas)', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    # Nuevo campo para el operador asignado
    operator = QuerySelectField('Operador Asignado', query_factory=get_users_for_pp, allow_blank=True, get_label='username', validators=[Optional()])
    # Nuevo campo para las horas reales
    actual_hours = FloatField('Horas Reales', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    required_skills = TextAreaField('Habilidades Requeridas (JSON)', validators=[Optional()]) # Reemplazado TODO con TextAreaField para JSON string
    parameters = TextAreaField('Parámetros del Proceso (JSON)', validators=[Optional()]) # Reemplazado TODO con TextAreaField para JSON string
    quality_checks = TextAreaField('Verificaciones de Calidad (JSON)', validators=[Optional()]) # Reemplazado TODO con TextAreaField para JSON string
    notes = TextAreaField('Notas', validators=[
        Optional(),
        Length(max=500)
    ])
    submit = SubmitField('Guardar Proceso')

class ProductionOrderForm(FlaskForm):
    id = HiddenField()
    product_id = SelectField('Producto', coerce=int, validators=[
        DataRequired()
    ])
    quantity = FloatField('Cantidad', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    planned_start = DateTimeField('Fecha de Inicio Planificada', 
                                format='%Y-%m-%d %H:%M',
                                validators=[DataRequired()])
    planned_end = DateTimeField('Fecha de Fin Planificada', 
                              format='%Y-%m-%d %H:%M',
                              validators=[DataRequired()])
    priority = SelectField('Prioridad', choices=[
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[
        Optional(),
        Length(max=500)
    ])

    def validate_planned_end(self, field):
        if field.data <= self.planned_start.data:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

class QualityCheckForm(FlaskForm):
    id = HiddenField()
    check_type = StringField('Tipo de Verificación', validators=[
        DataRequired(),
        Length(max=50)
    ])
    status = SelectField('Estado', choices=[
        ('pending', 'Pendiente'),
        ('passed', 'Aprobado'),
        ('failed', 'Rechazado')
    ], validators=[DataRequired()])
    result = TextAreaField('Resultado', validators=[
        Optional(),
        Length(max=500)
    ])
    check_date = DateTimeField('Fecha de Verificación', 
                             format='%Y-%m-%d %H:%M',
                             default=datetime.utcnow,
                             validators=[DataRequired()])

class ProductionOrderItemForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    production_order_id = HiddenField() # Para saber a qué orden pertenece
    material = QuerySelectField('Material', query_factory=get_materials_for_pp, allow_blank=False, get_label='name', validators=[DataRequired()])
    quantity_required = FloatField('Cantidad Requerida', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    actual_quantity = FloatField('Cantidad Usada', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    unit_price = FloatField('Precio Unitario', validators=[
        Optional(), # Puede no conocerse al planificar
        NumberRange(min=0)
    ])
    notes = TextAreaField('Notas', validators=[
        Optional(),
        Length(max=500)
    ])
    # subtotal y total_cost se calcularían automáticamente
    submit = SubmitField('Guardar Ítem')

# TODO: Add forms for ProductComponent and ProductProcess later 