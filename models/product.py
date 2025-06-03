from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    product_type = db.Column(db.String(50), nullable=False)  # Tanque, intercambiador, etc.
    material_type = db.Column(db.String(50), nullable=False)  # AISI304, etc.
    unit_of_measure = db.Column(db.String(20), nullable=False)  # unidad, kg, etc.
    standard_price = db.Column(db.Float)
    estimated_production_time = db.Column(db.Float)  # en horas
    weight = db.Column(db.Float)  # en kg
    dimensions = db.Column(db.String(50))  # formato: "LxWxH"
    technical_specs = db.Column(db.JSON)  # Especificaciones técnicas
    welding_specs = db.Column(db.JSON)  # Especificaciones de soldadura
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    components = db.relationship('ProductComponent', backref='product', cascade='all, delete-orphan')
    processes = db.relationship('ProductProcess', backref='product', cascade='all, delete-orphan')
    production_orders = db.relationship('ProductionOrder', backref='product')
    quality_standards = db.relationship('QualityStandard', backref='product')

    def __repr__(self):
        return f'<Product {self.code} - {self.name}>'

    def calculate_total_weight(self):
        """Calcula el peso total del producto sumando sus componentes"""
        return sum(component.weight for component in self.components)

    def get_required_processes(self):
        """Obtiene los procesos requeridos para la fabricación"""
        return sorted(self.processes, key=lambda x: x.sequence)

class ProductComponent(db.Model):
    __tablename__ = 'product_components'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Float)  # peso individual
    position = db.Column(db.String(50))  # posición en el producto
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    material = db.relationship('Material', backref='product_components')

    def __repr__(self):
        return f'<ProductComponent {self.id} - {self.material.name}>'

class ProductProcess(db.Model):
    __tablename__ = 'product_processes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    process_type = db.Column(db.String(50), nullable=False)  # soldadura_tig, corte, doblado, etc.
    sequence = db.Column(db.Integer, nullable=False)  # Orden del proceso
    estimated_time = db.Column(db.Float)  # Tiempo estimado en horas
    required_skills = db.Column(db.JSON)  # Habilidades requeridas
    parameters = db.Column(db.JSON)  # Parámetros específicos del proceso
    quality_checks = db.Column(db.JSON)  # Puntos de control de calidad
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProductProcess {self.id} - {self.process_type}>' 