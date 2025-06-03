from app import db
from datetime import datetime

class QualityCheckpoint(db.Model):
    __tablename__ = 'quality_checkpoints'

    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('quality_inspections.id'), nullable=False)
    checkpoint_type = db.Column(db.String(50), nullable=False) # Ej: 'visual', 'dimensional', 'prueba_funcionamiento'
    description = db.Column(db.Text)
    requirement = db.Column(db.String(255)) # Requisito o especificación a cumplir
    result_type = db.Column(db.String(20)) # Ej: 'pass/fail', 'measured_value', 'text'
    result = db.Column(db.Text) # Resultado registrado (True/False, valor, texto)
    status = db.Column(db.String(20), default='pending') # Ej: 'pending', 'passed', 'failed', 'skipped'
    notes = db.Column(db.Text)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id')) # Inspector que realizó este punto de control (opcional, si es diferente al de la inspección)
    inspection_date = db.Column(db.DateTime) # Fecha/hora de este punto de control (opcional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    inspector = db.relationship('User', foreign_keys=[inspector_id], backref='checkpoints_performed')

    def __repr__(self):
        return f'<QualityCheckpoint {self.id} - {self.checkpoint_type}>' 