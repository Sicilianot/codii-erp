from app import db
from datetime import datetime

class MaterialCategory(db.Model):
    __tablename__ = 'material_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6c757d')  # Color en formato hexadecimal
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    materials = db.relationship('Material', backref='category', lazy=True)

    def __repr__(self):
        return f'<MaterialCategory {self.name}>' 