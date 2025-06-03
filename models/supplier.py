from app import db
from datetime import datetime

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tax_id = db.Column(db.String(20))  # RUC/CIF
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    payment_terms = db.Column(db.String(50))  # Términos de pago
    delivery_terms = db.Column(db.String(50))  # Términos de entrega
    supplier_type = db.Column(db.String(50))  # Materiales, Servicios, etc.
    rating = db.Column(db.Float, default=0)  # Calificación del proveedor
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier')
    invoices = db.relationship('Invoice', backref='supplier')

    def __repr__(self):
        return f'<Supplier {self.code} - {self.name}>'

    def update_rating(self, new_rating):
        """Actualiza la calificación del proveedor"""
        self.rating = (self.rating + new_rating) / 2
        self.updated_at = datetime.utcnow()

    def get_purchase_history(self):
        """Obtiene el historial de compras al proveedor"""
        return self.purchase_orders.order_by(PurchaseOrder.created_at.desc()).all()

    def get_total_purchases(self):
        """Calcula el total de compras al proveedor"""
        return sum(order.total_amount for order in self.purchase_orders) 