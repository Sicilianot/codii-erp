from app import db
from datetime import datetime

class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    movement_number = db.Column(db.String(20), unique=True, nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # in, out, transfer
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float)  # Precio unitario al momento del movimiento
    reference_type = db.Column(db.String(20))  # purchase_order, production_order, sales_order, etc.
    reference_id = db.Column(db.Integer)  # ID del documento relacionado
    from_location = db.Column(db.String(50))  # Ubicación origen
    to_location = db.Column(db.String(50))  # Ubicación destino
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    creator = db.relationship('User', backref='created_movements')

    def __repr__(self):
        return f'<InventoryMovement {self.movement_number}>'

    def process_movement(self):
        """Procesa el movimiento y actualiza el stock del material"""
        material = self.material
        if self.movement_type == 'in':
            material.update_stock(self.quantity, 'in')
        elif self.movement_type == 'out':
            material.update_stock(self.quantity, 'out')
        elif self.movement_type == 'transfer':
            # En transferencias, el stock total no cambia
            pass
        db.session.commit()

class InventoryCount(db.Model):
    __tablename__ = 'inventory_counts'
    
    id = db.Column(db.Integer, primary_key=True)
    count_number = db.Column(db.String(20), unique=True, nullable=False)
    count_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')  # draft, in_progress, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relaciones
    items = db.relationship('InventoryCountItem', backref='inventory_count', cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_counts')

    def __repr__(self):
        return f'<InventoryCount {self.count_number}>'

    def complete_count(self):
        """Marca el conteo como completado"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        # Aquí se podrían procesar las diferencias encontradas

class InventoryCountItem(db.Model):
    __tablename__ = 'inventory_count_items'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_count_id = db.Column(db.Integer, db.ForeignKey('inventory_counts.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    system_quantity = db.Column(db.Float, nullable=False)  # Cantidad según el sistema
    counted_quantity = db.Column(db.Float)  # Cantidad contada físicamente
    difference = db.Column(db.Float)  # Diferencia entre sistema y conteo
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryCountItem {self.id} - {self.material.name}>'

    def calculate_difference(self):
        """Calcula la diferencia entre el sistema y el conteo físico"""
        if self.counted_quantity is not None:
            self.difference = self.counted_quantity - self.system_quantity
            return self.difference
        return None 