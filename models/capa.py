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
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    verification_method = db.Column(db.Text) # Cómo se verificará la efectividad
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    verification_date = db.Column(db.DateTime)
    effectiveness_status = db.Column(db.String(20)) # Ej: 'effective', 'not_effective'
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='capas_assigned')
    verifier = db.relationship('User', foreign_keys=[verified_by_id], backref='capas_verified')
    creator = db.relationship('User', foreign_keys=[created_by], backref='capas_created')

    # Relaciones polimórficas similares a QualityInspection para source_type/source_id

    def __repr__(self):
        return f'<CAPA {self.capa_number} - {self.status}>' 