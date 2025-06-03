from app import db
from datetime import datetime

class MaterialMovement(db.Model):
    __tablename__ = 'material_movements'

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'in' o 'out'
    quantity = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    user = db.relationship('User', backref='material_movements', lazy=True)

    def __repr__(self):
        return f'<MaterialMovement {self.material_id} - {self.type} - {self.quantity}>'

    @property
    def resulting_stock(self):
        if self.type == 'in':
            return self.material.current_stock
        return self.material.current_stock + self.quantity 