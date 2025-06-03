from app import db
from datetime import datetime

class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    material_type = db.Column(db.String(50), nullable=False)  # AISI304, Acero al Carbono, etc.
    unit_of_measure = db.Column(db.String(20), nullable=False)  # kg, m, piezas, etc.
    min_stock = db.Column(db.Float, default=0)
    max_stock = db.Column(db.Float, default=0)
    current_stock = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    location = db.Column(db.String(50))  # Ubicación en almacén
    specifications = db.Column(db.Text)  # Especificaciones técnicas
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    supplier = db.relationship('Supplier', backref='materials')
    inventory_movements = db.relationship('InventoryMovement', backref='material')
    purchase_orders = db.relationship('PurchaseOrderItem', backref='material')
    production_orders = db.relationship('ProductionOrderItem', backref='material')

    def __repr__(self):
        return f'<Material {self.code} - {self.name}>'

    def update_stock(self, quantity, movement_type):
        """Actualiza el stock del material según el tipo de movimiento"""
        if movement_type == 'in':
            self.current_stock += quantity
        elif movement_type == 'out':
            self.current_stock -= quantity
        self.updated_at = datetime.utcnow()

    def check_stock_level(self):
        """Verifica si el stock está por debajo del mínimo o por encima del máximo"""
        if self.current_stock < self.min_stock:
            return 'low'
        elif self.current_stock > self.max_stock:
            return 'high'
        return 'normal' 