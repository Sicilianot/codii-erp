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