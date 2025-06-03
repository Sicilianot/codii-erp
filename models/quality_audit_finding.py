from app import db
from datetime import datetime

class QualityAuditFinding(db.Model):
    __tablename__ = 'quality_audit_findings'

    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('quality_audits.id'), nullable=False)
    finding_type = db.Column(db.String(20), nullable=False) # Ej: 'conformity', 'non_conformity', 'observation'
    description = db.Column(db.Text, nullable=False)
    criteria = db.Column(db.Text) # Criterio de auditoría relacionado
    evidence = db.Column(db.Text) # Evidencia encontrada
    required_action = db.Column(db.Text) # Acción correctiva/preventiva si es NC
    status = db.Column(db.String(20), default='open') # Ej: 'open', 'closed'
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='audit_findings_assigned')

    def __repr__(self):
        return f'<QualityAuditFinding {self.id} - {self.finding_type}>' 