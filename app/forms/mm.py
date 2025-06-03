from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, HiddenField, SubmitField, DateField, DecimalField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Supplier, Material, MaterialMovement, MaterialCategory # Actualizada la importación
from datetime import date

def get_suppliers():
    return Supplier.query.all()

def get_materials():
    return Material.query.all()

class MaterialForm(FlaskForm):
    id = HiddenField()
    name = StringField('Nombre del Material', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descripción', validators=[Optional()])
    unit = StringField('Unidad de Medida', validators=[DataRequired(), Length(max=20)])
    initial_stock = FloatField('Stock Inicial', validators=[DataRequired()])
    submit = SubmitField('Guardar Material')

class MaterialMovementForm(FlaskForm):
    id = HiddenField()
    material_id = HiddenField('Material ID', validators=[
        DataRequired()
    ])
    adjustment_type = SelectField('Tipo de Ajuste', choices=[
        ('in', 'Entrada'),
        ('out', 'Salida')
    ], validators=[
        DataRequired()
    ])
    quantity = FloatField('Cantidad', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    notes = TextAreaField('Notas', validators=[
        Optional(),
        Length(max=500)
    ])

class MaterialCategoryForm(FlaskForm):
    id = HiddenField()
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

class SupplierForm(FlaskForm):
    id = HiddenField()
    name = StringField('Nombre del Proveedor', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Persona de Contacto', validators=[Optional(), Length(max=100)])
    phone = StringField('Teléfono', validators=[Optional(), Length(max=50)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Dirección', validators=[Optional()])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar Proveedor')

class PurchaseOrderForm(FlaskForm):
    id = HiddenField()
    supplier = QuerySelectField('Proveedor', query_factory=get_suppliers, allow_blank=True, get_label='name', validators=[DataRequired()])
    order_date = DateField('Fecha de la Orden', validators=[DataRequired()], default=date.today())
    status = SelectField('Estado', choices=[('pending', 'Pendiente'), ('approved', 'Aprobada'), ('rejected', 'Rechazada'), ('completed', 'Completada'), ('cancelled', 'Cancelada')], validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar Orden de Compra')

class PurchaseOrderItemForm(FlaskForm):
    id = HiddenField()
    material = QuerySelectField('Material', query_factory=get_materials, allow_blank=False, get_label='name', validators=[DataRequired()])
    quantity = DecimalField('Cantidad', validators=[DataRequired(), NumberRange(min=0.01)])
    unit_price = DecimalField('Precio Unitario', validators=[DataRequired(), NumberRange(min=0)])
    # subtotal se calcularía automáticamente
    submit = SubmitField('Guardar Ítem') 