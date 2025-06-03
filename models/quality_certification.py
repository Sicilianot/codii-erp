from app import db
from datetime import datetime

class QualityCertificate(db.Model):
    __tablename__ = 'quality_certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    certificate_type = db.Column(db.String(50), nullable=False)  # material, producto, proceso
    reference_type = db.Column(db.String(50), nullable=False)  # material, producto, proceso
    reference_id = db.Column(db.Integer, nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False)
    expiry_date = db.Column(db.DateTime)
    issuing_body = db.Column(db.String(100))
    standard = db.Column(db.String(100))  # Norma o estándar aplicable
    scope = db.Column(db.Text)
    test_results = db.Column(db.JSON)  # Resultados de pruebas
    attachments = db.Column(db.JSON)  # Archivos adjuntos
    status = db.Column(db.String(20), default='active')  # active, expired, revoked
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    creator = db.relationship('User', backref='created_certificates')

    def __repr__(self):
        return f'<QualityCertificate {self.certificate_number}>'

    def is_valid(self):
        """Verifica si el certificado es válido"""
        if self.status != 'active':
            return False
        if self.expiry_date and self.expiry_date < datetime.utcnow():
            return False
        return True

    def revoke(self, reason):
        """Revoca el certificado"""
        self.status = 'revoked'
        self.notes = f"Revocado: {reason}\n{self.notes}" if self.notes else f"Revocado: {reason}"
        self.updated_at = datetime.utcnow()

class QualityDocument(db.Model):
    __tablename__ = 'quality_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    document_number = db.Column(db.String(50), unique=True, nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # procedimiento, instrucción, formato
    title = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, review, approved, obsolete
    department = db.Column(db.String(50))
    category = db.Column(db.String(50))
    content = db.Column(db.Text)
    attachments = db.Column(db.JSON)  # Archivos adjuntos
    effective_date = db.Column(db.DateTime)
    review_date = db.Column(db.DateTime)
    next_review_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_documents')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_documents')
    revisions = db.relationship('DocumentRevision', backref='document', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<QualityDocument {self.document_number} - {self.title}>'

    def update_status(self, new_status):
        """Actualiza el estado del documento"""
        valid_statuses = ['draft', 'review', 'approved', 'obsolete']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'approved':
                self.effective_date = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def create_revision(self, version, changes, created_by):
        """Crea una nueva revisión del documento"""
        revision = DocumentRevision(
            document_id=self.id,
            version=version,
            changes=changes,
            created_by=created_by
        )
        self.revisions.append(revision)
        self.version = version
        self.updated_at = datetime.utcnow()
        return revision

class DocumentRevision(db.Model):
    __tablename__ = 'document_revisions'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('quality_documents.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    changes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    creator = db.relationship('User', backref='created_revisions')

    def __repr__(self):
        return f'<DocumentRevision {self.version} - {self.document.title}>' 