from app import db
from datetime import datetime

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')  # draft, sent, confirmed, received, cancelled
    total_amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    payment_terms = db.Column(db.String(100))
    delivery_terms = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_purchase_orders')

    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'

    def calculate_total(self):
        """Calcula el total de la orden de compra"""
        self.total_amount = sum(item.total_price for item in self.items)
        return self.total_amount

    def update_status(self, new_status):
        """Actualiza el estado de la orden de compra"""
        valid_statuses = ['draft', 'sent', 'confirmed', 'received', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    received_quantity = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PurchaseOrderItem {self.id} - {self.material.name}>'

    def calculate_total(self):
        """Calcula el total del item"""
        self.total_price = self.quantity * self.unit_price
        return self.total_price

    def update_received_quantity(self, quantity):
        """Actualiza la cantidad recibida"""
        self.received_quantity += quantity
        self.updated_at = datetime.utcnow()
        if self.received_quantity >= self.quantity:
            return True  # Indica que el item está completamente recibido
        return False 