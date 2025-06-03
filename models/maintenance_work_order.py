from app import db
from datetime import datetime

class MaintenanceWorkOrder(db.Model):
    __tablename__ = 'maintenance_work_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_number = db.Column(db.String(20), unique=True, nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
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
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    cost_center = db.Column(db.String(50))
    total_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    equipment = db.relationship('Equipment', backref='work_orders')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_work_orders')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_work_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_work_orders')
    tasks = db.relationship('WorkOrderTask', backref='work_order', cascade='all, delete-orphan')
    materials = db.relationship('WorkOrderMaterial', backref='work_order', cascade='all, delete-orphan')
    quality_checks = db.relationship('WorkOrderQualityCheck', backref='work_order', cascade='all, delete-orphan')

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
    work_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_work_orders.id'), nullable=False)
    task_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sequence = db.Column(db.Integer, nullable=False)  # Orden de ejecución
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    estimated_duration = db.Column(db.Float)  # en horas
    actual_duration = db.Column(db.Float)  # en horas
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    instructions = db.Column(db.Text)
    safety_instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assignee = db.relationship('User', backref='assigned_tasks')

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
    work_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_work_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    material = db.relationship('Material', backref='work_order_materials')

    def __repr__(self):
        return f'<WorkOrderMaterial {self.id} - {self.material.name}>'

    def calculate_total_cost(self):
        """Calcula el costo total del material"""
        self.total_cost = self.quantity * self.unit_price
        return self.total_cost

class WorkOrderQualityCheck(db.Model):
    __tablename__ = 'work_order_quality_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_work_orders.id'), nullable=False)
    check_type = db.Column(db.String(50), nullable=False)  # visual, funcional, dimensional, etc.
    description = db.Column(db.Text)
    standard = db.Column(db.String(100))  # Norma o estándar aplicable
    acceptance_criteria = db.Column(db.Text)
    measurement_value = db.Column(db.Float)
    measurement_unit = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')  # pending, passed, failed
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    performed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    inspector = db.relationship('User', backref='performed_quality_checks')

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