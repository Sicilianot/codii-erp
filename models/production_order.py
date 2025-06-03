from app import db
from datetime import datetime

class ProductionOrder(db.Model):
    __tablename__ = 'production_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, planned, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    actual_start_date = db.Column(db.DateTime)
    actual_end_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Nuevo campo para el costo total estimado
    estimated_total_cost = db.Column(db.Float, default=0.0)

    # Relaciones
    items = db.relationship('ProductionOrderItem', backref='production_order', cascade='all, delete-orphan')
    processes = db.relationship('ProductionProcess', backref='production_order', cascade='all, delete-orphan')
    quality_checks = db.relationship('QualityCheck', backref='production_order')
    creator = db.relationship('User', backref='created_production_orders')

    def __repr__(self):
        return f'<ProductionOrder {self.order_number}>'

    def calculate_estimated_hours(self):
        """Calcula las horas estimadas totales de la orden"""
        self.estimated_hours = sum(process.estimated_hours for process in self.processes)
        return self.estimated_hours

    def calculate_estimated_total_cost(self):
        """Calcula el costo total estimado de la orden sumando los costos de los ítems."""
        # Asegurarse de que los ítems están cargados si se usa esta función fuera de una consulta con joinedload
        # self.items se cargará si la relación se usa o si se hace joinedload
        total = sum((item.quantity_required * item.unit_price) for item in self.items) # Sumar costo por ítem
        self.estimated_total_cost = total
        return self.estimated_total_cost

    def update_status(self, new_status):
        """Actualiza el estado de la orden de producción"""
        valid_statuses = ['draft', 'planned', 'in_progress', 'completed', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'in_progress' and not self.actual_start_date:
                self.actual_start_date = datetime.utcnow()
            elif new_status == 'completed' and not self.actual_end_date:
                self.actual_end_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def update_order_status_from_processes(self):
        """Actualiza el estado de la orden basado en el estado de sus procesos."""
        if self.processes:
            all_processes_completed = all(process.status == 'completed' for process in self.processes)
            all_processes_cancelled = all(process.status == 'cancelled' for process in self.processes)
            any_process_in_progress = any(process.status == 'in_progress' for process in self.processes)
            any_process_cancelled = any(process.status == 'cancelled' for process in self.processes)

            if all_processes_completed:
                self.status = 'completed'
            elif any_process_in_progress:
                 self.status = 'in_progress'
            elif any_process_cancelled:
                 self.status = 'cancelled'
            elif all(process.status == 'pending' for process in self.processes) and self.status != 'draft':
                 self.status = 'planned'
            # TODO: Considerar otros estados como 'on hold' o 'planned'
            # Si no hay procesos, o todos son pending/cancelled/completed en alguna combinación, el estado podría ser 'planned' o 'draft'
            # Podríamos refinar la lógica según los estados de la orden (draft, planned, in_progress, completed, cancelled)

            # Lógica más simple: Si todos completados -> completed. Si alguno en progreso -> in_progress. Si alguno cancelado y ninguno en progreso -> cancelled. Si todos pendientes -> planned.
            if all_processes_completed:
                self.status = 'completed'
            elif any_process_in_progress:
                 self.status = 'in_progress'
            elif any_process_cancelled and not any_process_in_progress:
                 self.status = 'cancelled'
            elif all(process.status == 'pending' for process in self.processes):
                 self.status = 'planned'
            # Si no hay procesos, o una mezcla de completados/cancelados sin in_progress, el estado podría quedarse como estaba o ir a un estado neutral
            # Por ahora, esta lógica cubre los casos principales.

            self.updated_at = datetime.utcnow()
            db.session.add(self) # Asegurarse de que los cambios en la orden se reflejen

class ProductionOrderItem(db.Model):
    __tablename__ = 'production_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(20), nullable=False)
    estimated_quantity = db.Column(db.Float)  # Cantidad estimada necesaria
    actual_quantity = db.Column(db.Float)  # Cantidad real utilizada
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProductionOrderItem {self.id} - {self.material.name}>'

class ProductionProcess(db.Model):
    __tablename__ = 'production_processes'
    
    id = db.Column(db.Integer, primary_key=True)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_orders.id'), nullable=False)
    process_type = db.Column(db.String(50), nullable=False)  # soldadura_tig, corte, doblado, etc.
    sequence = db.Column(db.Integer, nullable=False)  # Orden del proceso
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    parameters = db.Column(db.JSON)  # Parámetros específicos del proceso (ej: amperaje, gas, etc.)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    operator = db.relationship('User', backref='assigned_processes')
    equipment = db.relationship('Equipment', backref='processes')
    quality_checks = db.relationship('QualityCheck', backref='production_process')

    def __repr__(self):
        return f'<ProductionProcess {self.id} - {self.process_type}>'

    def update_status(self, new_status):
        """Actualiza el estado del proceso"""
        valid_statuses = ['pending', 'in_progress', 'completed']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'in_progress' and not self.start_date:
                self.start_date = datetime.utcnow()
            elif new_status == 'completed' and not self.end_date:
                self.end_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False 