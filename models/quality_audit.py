from app import db
from datetime import datetime

class QualityAudit(db.Model):
    __tablename__ = 'quality_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_number = db.Column(db.String(50), unique=True, nullable=False)
    audit_type = db.Column(db.String(50), nullable=False)  # Ej: 'internal', 'external'
    scope = db.Column(db.Text)
    planned_date = db.Column(db.DateTime, nullable=False)
    actual_date = db.Column(db.DateTime)
    lead_auditor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    auditors = db.Column(db.Text)  # Puede ser una lista de nombres o IDs serializados
    audited_area = db.Column(db.String(100))
    status = db.Column(db.String(20), default='planned')  # Ej: 'planned', 'in_progress', 'completed', 'cancelled'
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    lead_auditor = db.relationship('User', foreign_keys=[lead_auditor_id], backref='audits_led')
    creator = db.relationship('User', foreign_keys=[created_by], backref='audits_created')
    findings = db.relationship('QualityAuditFinding', backref='audit', lazy='dynamic', cascade='all, delete-orphan')  # Actualizada la relación al nuevo nombre

    def __repr__(self):
        return f'<QualityAudit {self.audit_number}>'

    def update_status(self, new_status):
        """Actualiza el estado de la auditoría"""
        valid_statuses = ['planned', 'in_progress', 'completed', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'completed':
                self.actual_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def add_auditor(self, user_id, role):
        """Agrega un auditor al equipo"""
        team_member = AuditTeam(
            audit_id=self.id,
            user_id=user_id,
            role=role
        )
        self.auditors.append(team_member)
        return team_member

class AuditTeam(db.Model):
    __tablename__ = 'audit_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('quality_audits.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # lead_auditor, auditor, observer
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    user = db.relationship('User', backref='audit_team_memberships')

    def __repr__(self):
        return f'<AuditTeam {self.user.name} - {self.role}>'

class AuditFinding(db.Model):
    __tablename__ = 'audit_findings'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('quality_audits.id'), nullable=False)
    finding_type = db.Column(db.String(50), nullable=False)  # conformidad, no_conformidad, observación
    severity = db.Column(db.String(20))  # minor, major, critical
    clause = db.Column(db.String(50))  # Cláusula de la norma
    description = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.Text)
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
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_findings')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_findings')

    def __repr__(self):
        return f'<AuditFinding {self.id} - {self.finding_type}>'

    def update_status(self, new_status):
        """Actualiza el estado del hallazgo"""
        valid_statuses = ['open', 'in_progress', 'closed']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'closed':
                self.completion_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False 