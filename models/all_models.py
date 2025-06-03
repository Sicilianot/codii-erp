from app import db

# Consolidated model definitions will go here

from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Add content from models/material.py below

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
    inventory_movements = db.relationship('InventoryMovement', backref='material') # NOTE: InventoryMovement model needs to be defined
    purchase_orders = db.relationship('PurchaseOrderItem', backref='material') # NOTE: PurchaseOrderItem model needs to be defined
    production_orders = db.relationship('ProductionOrderItem', backref='material') # NOTE: ProductionOrderItem model needs to be defined

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

# Add content from models/supplier.py below

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
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier') # NOTE: PurchaseOrder model needs to be defined
    invoices = db.relationship('Invoice', backref='supplier') # NOTE: Invoice model needs to be defined

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

# Add content from models/purchase_order.py below

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
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', cascade='all, delete-orphan') # NOTE: PurchaseOrderItem model needs to be defined (defined below)
    creator = db.relationship('User', backref='created_purchase_orders') # NOTE: User model needs to be defined (defined above)

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

# Add content from models/production_order.py below

from app import db
from datetime import datetime

class ProductionOrder(db.Model):
    __tablename__ = 'production_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id')) # NOTE: Customer model needs to be defined
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id')) # NOTE: SalesOrder model needs to be defined
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
    items = db.relationship('ProductionOrderItem', backref='production_order', cascade='all, delete-orphan') # NOTE: ProductionOrderItem model needs to be defined (defined below)
    processes = db.relationship('ProductionProcess', backref='production_order', cascade='all, delete-orphan') # NOTE: ProductionProcess model needs to be defined (defined below)
    quality_checks = db.relationship('QualityCheck', backref='production_order') # NOTE: QualityCheck model needs to be defined
    creator = db.relationship('User', backref='created_production_orders') # NOTE: User model needs to be defined (defined above)

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
            elif any_process_cancelled and not any_process_in_progress:
                 self.status = 'cancelled'
            elif all(process.status == 'pending' for process in self.processes):
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
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id')) # NOTE: Equipment model needs to be defined
    parameters = db.Column(db.JSON)  # Parámetros específicos del proceso (ej: amperaje, gas, etc.)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    operator = db.relationship('User', backref='assigned_processes') # NOTE: User model needs to be defined (defined above)
    equipment = db.relationship('Equipment', backref='processes') # NOTE: Equipment model needs to be defined
    quality_checks = db.relationship('QualityCheck', backref='production_process') # NOTE: QualityCheck model needs to be defined

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

# Add content from models/maintenance_work_order.py below

from app import db
from datetime import datetime

class MaintenanceWorkOrder(db.Model):
    __tablename__ = 'maintenance_work_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_number = db.Column(db.String(20), unique=True, nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.id')) # NOTE: MaintenanceSchedule model needs to be defined
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False) # NOTE: Equipment model needs to be defined
    work_order_type = db.Column(db.String(50), nullable=False)  # preventivo, correctivo, predictivo
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    status = db.Column(db.String(20), default='draft')  # draft, approved, in_progress, completed, cancelled
    description = db.Column(db.Text, nullable=False)
    cause = db.Column(db.Text)  # Causa del mantenimiento
    solution = db.Column(db.Text)  # Solución aplicada
    estimated_duration = db.Column(db.Float)  # en horas
    actual_duration = db.Column(db.Float)  # en horas
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    cost_center = db.Column(db.String(50))
    total_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    equipment = db.relationship('Equipment', backref='work_orders') # NOTE: Equipment model needs to be defined
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_work_orders') # NOTE: User model needs to be defined (defined above)
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_work_orders') # NOTE: User model needs to be defined (defined above)
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_work_orders') # NOTE: User model needs to be defined (defined above)
    tasks = db.relationship('WorkOrderTask', backref='work_order', cascade='all, delete-orphan') # NOTE: WorkOrderTask model needs to be defined (defined below)
    materials = db.relationship('WorkOrderMaterial', backref='work_order', cascade='all, delete-orphan') # NOTE: WorkOrderMaterial model needs to be defined (defined below)
    quality_checks = db.relationship('WorkOrderQualityCheck', backref='work_order', cascade='all, delete-orphan') # NOTE: WorkOrderQualityCheck model needs to be defined (defined below)

    def __repr__(self):
        return f'<MaintenanceWorkOrder {self.work_order_number}>'

    def update_status(self, new_status):
        """Actualiza el estado de la orden de trabajo"""
        valid_statuses = ['draft', 'approved', 'in_progress', 'completed', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'in_progress' and not self.start_date:
                self.start_date = datetime.utcnow()
            elif new_status == 'completed' and not self.end_date:
                self.end_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def calculate_total_cost(self):
        """Calcula el costo total de la orden de trabajo"""
        labor_cost = self.actual_duration * 100  # Costo por hora de mano de obra
        materials_cost = sum(material.total_cost for material in self.materials)
        self.total_cost = labor_cost + materials_cost
        return self.total_cost

class WorkOrderTask(db.Model):
    __tablename__ = 'work_order_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_work_orders.id'), nullable=False) # NOTE: MaintenanceWorkOrder model needs to be defined (defined above)
    task_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sequence = db.Column(db.Integer, nullable=False)  # Orden de ejecución
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    estimated_duration = db.Column(db.Float)  # en horas
    actual_duration = db.Column(db.Float)  # en horas
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    instructions = db.Column(db.Text)
    safety_instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assignee = db.relationship('User', backref='assigned_tasks') # NOTE: User model needs to be defined (defined above)

    def __repr__(self):
        return f'<WorkOrderTask {self.task_number} - {self.name}>'

    def update_status(self, new_status):
        """Actualiza el estado de la tarea"""
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

class WorkOrderMaterial(db.Model):
    __tablename__ = 'work_order_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_work_orders.id'), nullable=False) # NOTE: MaintenanceWorkOrder model needs to be defined (defined above)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False) # NOTE: Material model needs to be defined (defined above)
    quantity = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    material = db.relationship('Material', backref='work_order_materials') # NOTE: Material model needs to be defined (defined above)

    def __repr__(self):
        return f'<WorkOrderMaterial {self.id} - {self.material.name}>'

    def calculate_total_cost(self):
        """Calcula el costo total del material"""
        self.total_cost = self.quantity * self.unit_price
        return self.total_cost

class WorkOrderQualityCheck(db.Model):
    __tablename__ = 'work_order_quality_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_work_orders.id'), nullable=False) # NOTE: MaintenanceWorkOrder model needs to be defined (defined above)
    check_type = db.Column(db.String(50), nullable=False)  # visual, funcional, dimensional, etc.
    description = db.Column(db.Text)
    standard = db.Column(db.String(100))  # Norma o estándar aplicable
    acceptance_criteria = db.Column(db.Text)
    measurement_value = db.Column(db.Float)
    measurement_unit = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')  # pending, passed, failed
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    performed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    inspector = db.relationship('User', backref='performed_quality_checks') # NOTE: User model needs to be defined (defined above)

    def __repr__(self):
        return f'<WorkOrderQualityCheck {self.id} - {self.check_type}>'

    def evaluate_result(self, value, performed_by):
        """Evalúa el resultado del punto de control"""
        self.measurement_value = value
        self.performed_by = performed_by
        self.performed_at = datetime.utcnow()
        # Aquí se implementaría la lógica de evaluación según los criterios de aceptación
        self.status = 'passed' if self._meets_criteria(value) else 'failed'
        self.updated_at = datetime.utcnow()

    def _meets_criteria(self, value):
        """Evalúa si el valor cumple con los criterios de aceptación"""
        # Implementación básica - se debe personalizar según necesidades
        return True

# Add content from models/capa.py below

from app import db
from datetime import datetime

class CAPA(db.Model):
    __tablename__ = 'capas'

    id = db.Column(db.Integer, primary_key=True)
    capa_number = db.Column(db.String(50), unique=True, nullable=False)
    capa_type = db.Column(db.String(20), nullable=False) # Ej: 'corrective', 'preventive'
    source_type = db.Column(db.String(50)) # Ej: 'non_conformity', 'audit_finding', 'customer_feedback'
    source_id = db.Column(db.Integer) # ID de la fuente (NonConformity, AuditFinding, etc.)
    description = db.Column(db.Text, nullable=False) # Descripción del problema o hallazgo que origina la CAPA
    root_cause = db.Column(db.Text) # Análisis de causa raíz
    proposed_action = db.Column(db.Text) # Acción propuesta
    implemented_action = db.Column(db.Text) # Acción implementada
    status = db.Column(db.String(20), default='open') # Ej: 'open', 'in_progress', 'implemented', 'verified', 'closed'
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    due_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    verification_method = db.Column(db.Text) # Cómo se verificará la efectividad
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined (defined above)
    verification_date = db.Column(db.DateTime)
    effectiveness_status = db.Column(db.String(20)) # Ej: 'effective', 'not_effective'
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # NOTE: User model needs to be defined (defined above)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='capas_assigned') # NOTE: User model needs to be defined (defined above)
    verifier = db.relationship('User', foreign_keys=[verified_by_id], backref='capas_verified') # NOTE: User model needs to be defined (defined above)
    creator = db.relationship('User', foreign_keys=[created_by], backref='capas_created') # NOTE: User model needs to be defined (defined above)

    # Relaciones polimórficas similares a QualityInspection para source_type/source_id

    def __repr__(self):
        return f'<CAPA {self.capa_number} - {self.status}>'

# Add content from models/material_category.py below

from app import db
from datetime import datetime

class MaterialCategory(db.Model):
    __tablename__ = 'material_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6c757d')  # Color en formato hexadecimal
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    materials = db.relationship('Material', backref='category', lazy=True) # NOTE: Material model needs to be defined (defined above)

    def __repr__(self):
        return f'<MaterialCategory {self.name}>'

# Add content from models/material_movement.py below

from app import db
from datetime import datetime

class MaterialMovement(db.Model):
    __tablename__ = 'material_movements'

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False) # NOTE: Material model needs to be defined (defined above)
    type = db.Column(db.String(20), nullable=False)  # 'in' o 'out'
    quantity = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # NOTE: User model needs to be defined (defined above)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    user = db.relationship('User', backref='material_movements', lazy=True) # NOTE: User model needs to be defined (defined above)

    def __repr__(self):
        return f'<MaterialMovement {self.material_id} - {self.type} - {self.quantity}>'

    @property
    def resulting_stock(self):
        if self.type == 'in':
            return self.material.current_stock
        return self.material.current_stock + self.quantity

# Add content from models/product.py below

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
    components = db.relationship('ProductComponent', backref='product', cascade='all, delete-orphan') # NOTE: ProductComponent model needs to be defined (defined below)
    processes = db.relationship('ProductProcess', backref='product', cascade='all, delete-orphan') # NOTE: ProductProcess model needs to be defined (defined below)
    production_orders = db.relationship('ProductionOrder', backref='product') # NOTE: ProductionOrder model needs to be defined (defined above)
    quality_standards = db.relationship('QualityStandard', backref='product') # NOTE: QualityStandard model needs to be defined

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
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False) # NOTE: Product model needs to be defined (defined above)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False) # NOTE: Material model needs to be defined (defined above)
    quantity = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Float)  # peso individual
    position = db.Column(db.String(50))  # posición en el producto
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    material = db.relationship('Material', backref='product_components') # NOTE: Material model needs to be defined (defined above)

    def __repr__(self):
        return f'<ProductComponent {self.id} - {self.material.name}>'

class ProductProcess(db.Model):
    __tablename__ = 'product_processes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False) # NOTE: Product model needs to be defined (defined above)
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

# Add content from models/product_category.py below

from app import db
from datetime import datetime

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con Product (si existe)
    # products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<ProductCategory {self.name}>'

# Add content from models/quality_inspection.py below

from app import db
from datetime import datetime

class QualityInspection(db.Model):
    __tablename__ = 'quality_inspections'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_number = db.Column(db.String(50), unique=True, nullable=False)
    inspection_type = db.Column(db.String(50), nullable=False)  # Ej: 'receiving', 'in_process', 'final'
    status = db.Column(db.String(20), default='pending')  # Ej: 'pending', 'in_progress', 'completed', 'cancelled'
    reference_type = db.Column(db.String(50))  # Ej: 'material', 'product', 'production_order'
    reference_id = db.Column(db.Integer)  # ID de la referencia (Material, Product, ProductionOrder, etc.)
    inspection_date = db.Column(db.DateTime, default=datetime.utcnow)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    result = db.Column(db.String(20))  # Ej: 'accepted', 'rejected', 'conditional'
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    inspector = db.relationship('User', foreign_keys=[inspector_id], backref='inspections_performed')
    creator = db.relationship('User', foreign_keys=[created_by], backref='inspections_created')
    checkpoints = db.relationship('QualityCheckpoint', backref='inspection', lazy='dynamic', cascade='all, delete-orphan')
    non_conformities = db.relationship('QualityNonConformity', backref='inspection', lazy='dynamic')  # Relación con No Conformidades

    # Relaciones polimórficas o campos de referencia flexibles podrían ser necesarios
    # para relacionar inspecciones con diferentes tipos de objetos (Material, Product, etc.)
    # Por ahora, usamos reference_type y reference_id.

    def __repr__(self):
        return f'<QualityInspection {self.inspection_number}>'

    def update_status(self, new_status):
        """Actualiza el estado de la inspección"""
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False

    def calculate_completion(self):
        """Calcula el porcentaje de completitud de la inspección"""
        if not self.checkpoints:
            return 0
        completed = sum(1 for cp in self.checkpoints if cp.status == 'completed')
        return (completed / len(self.checkpoints)) * 100

class QualityCheckpoint(db.Model):
    __tablename__ = 'quality_checkpoints'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('quality_inspections.id'), nullable=False)
    checkpoint_type = db.Column(db.String(50), nullable=False)  # dimensional, visual, funcional, etc.
    description = db.Column(db.Text)
    standard = db.Column(db.String(100))  # Norma o estándar aplicable
    acceptance_criteria = db.Column(db.Text)
    measurement_value = db.Column(db.Float)
    measurement_unit = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')  # pending, passed, failed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<QualityCheckpoint {self.id} - {self.checkpoint_type}>'

    def evaluate_result(self, value):
        """Evalúa el resultado del punto de control"""
        self.measurement_value = value
        # Aquí se implementaría la lógica de evaluación según los criterios de aceptación
        self.status = 'passed' if self._meets_criteria(value) else 'failed'
        self.updated_at = datetime.utcnow()

    def _meets_criteria(self, value):
        """Evalúa si el valor cumple con los criterios de aceptación"""
        # Implementación básica - se debe personalizar según necesidades
        return True

class NonConformity(db.Model):
    __tablename__ = 'non_conformities'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('quality_inspections.id'), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # minor, major, critical
    description = db.Column(db.Text, nullable=False)
    root_cause = db.Column(db.Text)
    corrective_action = db.Column(db.Text)
    preventive_action = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, in_progress, closed
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    verification_date = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_non_conformities')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_non_conformities')

    def __repr__(self):
        return f'<NonConformity {self.id} - {self.severity}>'

    def update_status(self, new_status):
        """Actualiza el estado de la no conformidad"""
        valid_statuses = ['open', 'in_progress', 'closed']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'closed':
                self.completion_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False 

class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    issue_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    issued_by = db.Column(db.String(100))
    standard_id = db.Column(db.Integer, db.ForeignKey('quality_standards.id')) # NOTE: QualityStandard model needs to be defined
    # TODO: Add field for file path
    file_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    standard = db.relationship('QualityStandard', backref='certificates') # NOTE: QualityStandard model needs to be defined

    def __repr__(self):
        return f'<Certificate {self.name}>'

# Add content from models/quality_document.py below

from app import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    document_type = db.Column(db.String(50), nullable=False) # ej: procedure, work_instruction, form, policy
    version = db.Column(db.String(10), default='1.0')
    effective_date = db.Column(db.DateTime)
    review_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft') # ej: draft, approved, obsolete
    # TODO: Add field for file path
    file_path = db.Column(db.String(255))
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id')) # NOTE: User model needs to be defined
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    issuer = db.relationship('User', foreign_keys=[issued_by], backref='issued_documents') # NOTE: User model needs to be defined
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_documents') # NOTE: User model needs to be defined
    # TODO: Add relationship to CAPAs or other related items if needed

    def __repr__(self):
        return f'<Document {self.title} v{self.version}>'

# Add content from models/quality_audit.py below 