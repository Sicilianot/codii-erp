from app import db
from datetime import datetime

class QualityNonConformity(db.Model):
    __tablename__ = 'quality_non_conformities'

    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('quality_inspections.id')) # Puede estar ligada a inspección o auditoría
    audit_id = db.Column(db.Integer, db.ForeignKey('quality_audits.id'))
    severity = db.Column(db.String(20), nullable=False) # Ej: 'minor', 'major', 'critical'
    description = db.Column(db.Text, nullable=False)
    root_cause = db.Column(db.Text)
    corrective_action = db.Column(db.Text)
    preventive_action = db.Column(db.Text)
    status = db.Column(db.String(20), default='open') # Ej: 'open', 'in_progress', 'implemented', 'verified', 'closed'
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    verification_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='non_conformities_assigned')
    verifier = db.relationship('User', foreign_keys=[verified_by_id], backref='non_conformities_verified')
    creator = db.relationship('User', foreign_keys=[created_by], backref='non_conformities_created')
    # inspection = db.relationship('Inspection', backref='non_conformities') # Relación definida en Inspection
    audit = db.relationship('QualityAudit', backref='non_conformities') # Actualizada la relación al nuevo nombre

    def __repr__(self):
        return f'<QualityNonConformity {self.id} - {self.status}>' 