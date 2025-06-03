from app import db
from datetime import datetime

class MaintenancePlan(db.Model):
    __tablename__ = 'maintenance_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # preventivo, predictivo, condicional
    frequency_type = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, yearly
    frequency_value = db.Column(db.Integer, nullable=False)  # valor de la frecuencia
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, inactive, completed
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    estimated_duration = db.Column(db.Float)  # en horas
    required_skills = db.Column(db.JSON)  # Habilidades requeridas
    required_tools = db.Column(db.JSON)  # Herramientas requeridas
    required_parts = db.Column(db.JSON)  # Partes requeridas
    instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    equipment = db.relationship('Equipment', backref='maintenance_plans')
    creator = db.relationship('User', backref='created_maintenance_plans')
    tasks = db.relationship('MaintenanceTask', backref='plan', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<MaintenancePlan {self.plan_number} - {self.name}>'

    def update_status(self, new_status):
        """Actualiza el estado del plan"""
        valid_statuses = ['active', 'inactive', 'completed']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False

    def calculate_next_due_date(self, last_completion_date):
        """Calcula la próxima fecha de vencimiento"""
        if self.frequency_type == 'daily':
            return last_completion_date + timedelta(days=self.frequency_value)
        elif self.frequency_type == 'weekly':
            return last_completion_date + timedelta(weeks=self.frequency_value)
        elif self.frequency_type == 'monthly':
            return last_completion_date + timedelta(days=30*self.frequency_value)
        elif self.frequency_type == 'yearly':
            return last_completion_date + timedelta(days=365*self.frequency_value)
        return None

class MaintenanceTask(db.Model):
    __tablename__ = 'maintenance_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('maintenance_plans.id'), nullable=False)
    task_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sequence = db.Column(db.Integer, nullable=False)  # Orden de ejecución
    estimated_duration = db.Column(db.Float)  # en horas
    required_skills = db.Column(db.JSON)  # Habilidades requeridas
    required_tools = db.Column(db.JSON)  # Herramientas requeridas
    required_parts = db.Column(db.JSON)  # Partes requeridas
    instructions = db.Column(db.Text)
    safety_instructions = db.Column(db.Text)
    quality_checks = db.Column(db.JSON)  # Puntos de control de calidad
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MaintenanceTask {self.task_number} - {self.name}>'

class MaintenanceSchedule(db.Model):
    __tablename__ = 'maintenance_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('maintenance_plans.id'), nullable=False)
    schedule_number = db.Column(db.String(20), unique=True, nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    actual_start_date = db.Column(db.DateTime)
    actual_end_date = db.Column(db.DateTime)
    actual_duration = db.Column(db.Float)  # en horas
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    plan = db.relationship('MaintenancePlan', backref='schedules')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_maintenance')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_schedules')
    work_orders = db.relationship('MaintenanceWorkOrder', backref='schedule', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<MaintenanceSchedule {self.schedule_number}>'

    def update_status(self, new_status):
        """Actualiza el estado del programa"""
        valid_statuses = ['scheduled', 'in_progress', 'completed', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'in_progress' and not self.actual_start_date:
                self.actual_start_date = datetime.utcnow()
            elif new_status == 'completed' and not self.actual_end_date:
                self.actual_end_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False 