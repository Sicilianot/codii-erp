from app import db
from datetime import datetime

class QualityDocument(db.Model):
    __tablename__ = 'quality_documents'

    id = db.Column(db.Integer, primary_key=True)
    document_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(20), default='1.0')
    document_type = db.Column(db.String(50)) # Ej: 'procedure', 'manual', 'policy', 'instruction'
    issue_date = db.Column(db.DateTime, nullable=False)
    revision_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active') # Ej: 'active', 'obsolete'
    file_path = db.Column(db.String(255), nullable=False) # Ruta al archivo del documento
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    creator = db.relationship('User', foreign_keys=[created_by], backref='documents_created')

    def __repr__(self):
        return f'<QualityDocument {self.document_code}>' 