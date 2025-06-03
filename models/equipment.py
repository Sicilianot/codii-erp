from app import db
from datetime import datetime

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    equipment_type = db.Column(db.String(50), nullable=False)  # soldadora_tig, cortadora, etc.
    model = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    manufacturer = db.Column(db.String(100))
    purchase_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, maintenance, inactive
    location = db.Column(db.String(50))
    specifications = db.Column(db.JSON)  # Especificaciones técnicas
    maintenance_schedule = db.Column(db.JSON)  # Programa de mantenimiento
    last_maintenance = db.Column(db.DateTime)
    next_maintenance = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    maintenance_records = db.relationship('MaintenanceRecord', backref='equipment', cascade='all, delete-orphan')
    calibrations = db.relationship('Calibration', backref='equipment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Equipment {self.code} - {self.name}>'

    def update_status(self, new_status):
        """Actualiza el estado del equipo"""
        valid_statuses = ['active', 'maintenance', 'inactive']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False

    def schedule_maintenance(self, maintenance_date):
        """Programa el próximo mantenimiento"""
        self.next_maintenance = maintenance_date
        self.updated_at = datetime.utcnow()

class MaintenanceRecord(db.Model):
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)  # preventivo, correctivo
    description = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    cost = db.Column(db.Float)
    parts_replaced = db.Column(db.JSON)  # Lista de partes reemplazadas
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    technician = db.relationship('User', backref='performed_maintenance')

    def __repr__(self):
        return f'<MaintenanceRecord {self.id} - {self.equipment.name}>'

    def complete_maintenance(self, end_date=None):
        """Marca el mantenimiento como completado"""
        self.end_date = end_date or datetime.utcnow()
        self.updated_at = datetime.utcnow()

class Calibration(db.Model):
    __tablename__ = 'calibrations'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    calibration_type = db.Column(db.String(50), nullable=False)
    calibration_date = db.Column(db.DateTime, nullable=False)
    next_calibration_date = db.Column(db.DateTime)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    results = db.Column(db.JSON)  # Resultados de la calibración
    certificate_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    technician = db.relationship('User', backref='performed_calibrations')

    def __repr__(self):
        return f'<Calibration {self.id} - {self.equipment.name}>'

    def schedule_next_calibration(self, next_date):
        """Programa la próxima calibración"""
        self.next_calibration_date = next_date
        self.updated_at = datetime.utcnow() 