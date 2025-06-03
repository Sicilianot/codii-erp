from app import db
from datetime import datetime

class QualityCertificate(db.Model):
    __tablename__ = 'quality_certificates'

    id = db.Column(db.Integer, primary_key=True)
    certificate_number = db.Column(db.String(100), unique=True, nullable=False)
    certificate_type = db.Column(db.String(50)) # Ej: 'material', 'product', 'process', 'system'
    reference_type = db.Column(db.String(50)) # Ej: 'material', 'product', 'supplier'
    reference_id = db.Column(db.Integer) # ID de la referencia
    issue_date = db.Column(db.DateTime, nullable=False)
    expiry_date = db.Column(db.DateTime)
    issued_by = db.Column(db.String(100))
    file_path = db.Column(db.String(255)) # Ruta al archivo del certificado
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    creator = db.relationship('User', foreign_keys=[created_by], backref='certificates_created')

    def __repr__(self):
        return f'<QualityCertificate {self.certificate_number}>' 