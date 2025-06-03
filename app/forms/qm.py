from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField, FloatField, DateField, HiddenField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, AnyOf, NumberRange, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from models import QualityInspection, QualityCheckpoint, QualityNonConformity, QualityCertificate, QualityDocument, QualityAudit, QualityAuditFinding, User, CAPA # Actualizada la importación
from datetime import date, datetime # Importar date para el default y datetime para el default
from flask_wtf.file import FileField, FileAllowed, FileRequired # Importar FileField y validadores

def get_active_users():
    return User.query.filter_by(is_active=True).all()

# --- Query Factories --- #

def get_users():
    return User.query.order_by(User.username).all()

def get_inspections():
    return QualityInspection.query.order_by(QualityInspection.inspection_number).all()

def get_audits():
    return QualityAudit.query.order_by(QualityAudit.audit_number).all()

def get_non_conformities():
    return QualityNonConformity.query.order_by(QualityNonConformity.id).all() # O por otro campo

# --- Formularios para Gestión de Calidad (QM) ---

class InspectionForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    inspection_number = StringField('Número de Inspección', validators=[DataRequired(), Length(max=64)])
    inspection_type = SelectField('Tipo de Inspección', choices=[('', 'Seleccionar'), ('incoming', 'Entrada'), ('in-process', 'En Proceso'), ('final', 'Final')], validators=[DataRequired()])
    reference_type = SelectField('Tipo de Referencia', choices=[('', 'Ninguna'), ('material', 'Material'), ('production_order', 'Orden de Producción')], validators=[Optional()])
    reference_id = StringField('ID de Referencia', validators=[Optional(), Length(max=64)])
    status = SelectField('Estado', choices=[('planned', 'Planificada'), ('in_progress', 'En Progreso'), ('completed', 'Completada'), ('cancelled', 'Cancelada')], validators=[DataRequired()])
    due_date = DateField('Fecha Límite', validators=[Optional()])
    inspector_id = QuerySelectField('Inspector Asignado', query_factory=get_active_users, get_label='username', allow_blank=True, blank_text='-- Seleccionar Usuario --', validators=[Optional()]) # Usar la función actualizada
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Inspección')

class CheckpointForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    description = TextAreaField('Descripción del Punto de Control', validators=[DataRequired(), Length(max=256)])
    standard = StringField('Estándar o Especificación', validators=[Optional(), Length(max=128)])
    acceptance_criteria = StringField('Criterios de Aceptación', validators=[Optional(), Length(max=128)])
    measurement_value = FloatField('Valor Medido', validators=[Optional()])
    measurement_unit = StringField('Unidad de Medida', validators=[Optional(), Length(max=16)])
    status = SelectField('Estado', choices=[('not_checked', 'Sin Revisar'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado')], validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Punto de Control')

class NonConformityForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    severity = SelectField('Severidad', choices=[('', 'Seleccionar'), ('minor', 'Menor'), ('major', 'Mayor'), ('critical', 'Crítica')], validators=[DataRequired()])
    description = TextAreaField('Descripción de la No Conformidad', validators=[DataRequired(), Length(max=500)])
    root_cause = TextAreaField('Causa Raíz', validators=[Optional(), Length(max=500)])
    corrective_action = TextAreaField('Acción Correctiva', validators=[Optional(), Length(max=500)])
    preventive_action = TextAreaField('Acción Preventiva', validators=[Optional(), Length(max=500)])
    status = SelectField('Estado', choices=[('open', 'Abierta'), ('in_progress', 'En Progreso'), ('closed', 'Cerrada')], validators=[DataRequired()])
    assigned_to_id = QuerySelectField('Asignado A', query_factory=get_active_users, get_label='username', allow_blank=True, blank_text='-- Seleccionar Usuario --', validators=[Optional()]) # Usar la función actualizada
    due_date = DateField('Fecha Límite', validators=[Optional()])
    completion_date = DateField('Fecha de Cierre', validators=[Optional()])
    verified_by_id = QuerySelectField('Verificado Por', query_factory=get_active_users, get_label='username', allow_blank=True, blank_text='-- Seleccionar Usuario --', validators=[Optional()]) # Usar la función actualizada
    verification_date = DateField('Fecha de Verificación', validators=[Optional()])
    notes = TextAreaField('Notas Adicionales', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar No Conformidad')

class CertificateForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    certificate_number = StringField('Número de Certificado', validators=[DataRequired(), Length(max=64)])
    certificate_type = SelectField('Tipo de Certificado', choices=[('', 'Seleccionar'), ('iso', 'ISO'), ('product', 'Producto')], validators=[DataRequired()])
    reference_type = SelectField('Tipo de Referencia', choices=[('', 'Ninguna'), ('material', 'Material'), ('product', 'Producto'), ('supplier', 'Proveedor')], validators=[Optional()])
    reference_id = StringField('ID de Referencia', validators=[Optional(), Length(max=64)])
    issue_date = DateField('Fecha de Emisión', validators=[DataRequired()], default=date.today)
    expiry_date = DateField('Fecha de Vencimiento', validators=[Optional()])
    issued_by = StringField('Emitido Por', validators=[DataRequired(), Length(max=128)])
    certificate_file = FileField('Archivo de Certificado', validators=[FileRequired(), FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Solo se permiten archivos PDF, JPG, JPEG o PNG!')])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Certificado')

class DocumentForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    document_code = StringField('Código de Documento', validators=[DataRequired(), Length(max=64)])
    title = StringField('Título', validators=[DataRequired(), Length(max=128)])
    version = StringField('Versión', validators=[DataRequired(), Length(max=16)])
    document_type = SelectField('Tipo de Documento', choices=[('', 'Seleccionar'), ('manual', 'Manual'), ('procedure', 'Procedimiento'), ('policy', 'Política')], validators=[DataRequired()])
    issue_date = DateField('Fecha de Emisión', validators=[DataRequired()], default=date.today)
    revision_date = DateField('Fecha de Revisión', validators=[Optional()])
    status = SelectField('Estado', choices=[('draft', 'Borrador'), ('active', 'Activo'), ('obsolete', 'Obsoleto')], validators=[DataRequired()])
    document_file = FileField('Archivo de Documento', validators=[FileRequired(), FileAllowed(['pdf', 'doc', 'docx', 'xlsx', 'pptx'], 'Solo se permiten archivos PDF, DOC, DOCX, XLSX o PPTX!')])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Documento')

class AuditForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    audit_number = StringField('Número de Auditoría', validators=[DataRequired(), Length(max=64)])
    audit_type = SelectField('Tipo de Auditoría', choices=[('', 'Seleccionar'), ('internal', 'Interna'), ('external', 'Externa'), ('supplier', 'Proveedor')], validators=[DataRequired()])
    scope = TextAreaField('Alcance', validators=[DataRequired(), Length(max=500)])
    planned_date = DateField('Fecha Planificada', validators=[DataRequired()])
    executed_date = DateField('Fecha de Ejecución', validators=[Optional()])
    status = SelectField('Estado', choices=[('planned', 'Planificada'), ('in_progress', 'En Progreso'), ('completed', 'Completada'), ('cancelled', 'Cancelada')], validators=[DataRequired()])
    lead_auditor_id = QuerySelectField('Auditor Líder', query_factory=get_active_users, get_label='username', allow_blank=True, blank_text='-- Seleccionar Usuario --', validators=[Optional()]) # Usar la función actualizada
    audited_area = StringField('Área Auditada', validators=[Optional(), Length(max=128)])
    report_date = DateField('Fecha de Informe', validators=[Optional()])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Auditoría')

class AuditFindingForm(FlaskForm):
    id = HiddenField() # Añadido para edición
    finding_type = SelectField('Tipo de Hallazgo', choices=[('', 'Seleccionar'), ('conformity', 'Conformidad'), ('observation', 'Observación'), ('non_conformity', 'No Conformidad'), ('major_nc', 'No Conformidad Mayor')], validators=[DataRequired()])
    description = TextAreaField('Descripción del Hallazgo', validators=[DataRequired(), Length(max=500)])
    severity = SelectField('Severidad', choices=[('', 'Seleccionar'), ('low', 'Baja'), ('medium', 'Media'), ('high', 'Alta')], validators=[DataRequired()])
    status = SelectField('Estado', choices=[('open', 'Abierto'), ('closed', 'Cerrado')], validators=[DataRequired()])
    assigned_to_id = QuerySelectField('Asignado A', query_factory=get_active_users, get_label='username', allow_blank=True, blank_text='-- Seleccionar Usuario --', validators=[Optional()]) # Usar la función actualizada
    due_date = DateField('Fecha Límite', validators=[Optional()])
    completion_date = DateField('Fecha de Cierre', validators=[Optional()])
    verified_by_id = QuerySelectField('Verificado Por', query_factory=get_active_users, get_label='username', allow_blank=True, blank_text='-- Seleccionar Usuario --', validators=[Optional()]) # Usar la función actualizada
    verification_date = DateField('Fecha de Verificación', validators=[Optional()])
    notes = TextAreaField('Notas Adicionales', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Hallazgo')

class QualityInspectionForm(FlaskForm):
    id = HiddenField()
    # inspection_number se podría generar automáticamente
    inspection_type = SelectField('Tipo de Inspección', choices=[
        ('receiving', 'Recepción'),
        ('in_process', 'En Proceso'),
        ('final', 'Final'),
        ('other', 'Otro')
    ], validators=[DataRequired()])
    # Campos para la referencia (Material, Producto, OP, etc.) - se manejarían con lógica en la ruta o campos condicionales
    # Por ahora, solo notas y resultado general
    status = SelectField('Estado', choices=[
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada')
    ], validators=[DataRequired()])
    inspection_date = DateTimeField('Fecha de Inspección', format='%Y-%m-%d %H:%M', default=datetime.utcnow, validators=[DataRequired()])
    inspector = QuerySelectField('Inspector', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    result = SelectField('Resultado General', choices=[
        ('', 'Seleccionar...'), # Opción vacía inicial
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('conditional', 'Aceptación Condicional')
    ], validators=[Optional()])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar Inspección')

class QualityCheckpointForm(FlaskForm):
    id = HiddenField()
    inspection_id = HiddenField() # Para relacionar con la inspección padre
    checkpoint_type = StringField('Tipo de Punto de Control', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Descripción', validators=[Optional()])
    requirement = StringField('Requisito/Estándar', validators=[Optional(), Length(max=255)])
    result_type = SelectField('Tipo de Resultado', choices=[
        ('pass/fail', 'Pasa/Falla'),
        ('measured_value', 'Valor Medido'),
        ('text', 'Texto Libre')
    ], validators=[DataRequired()])
    # Campo único para el resultado, su interpretación depende de result_type
    result = TextAreaField('Resultado', validators=[Optional()]) # Usamos TextAreaField para flexibilidad
    measurement_value = FloatField('Valor Medido', validators=[Optional(), NumberRange(min=0)]) # Campo específico si result_type es 'measured_value'
    measurement_unit = StringField('Unidad de Medida', validators=[Optional(), Length(max=20)])
    status = SelectField('Estado', choices=[
        ('pending', 'Pendiente'),
        ('passed', 'Pasa'),
        ('failed', 'Falla'),
        ('skipped', 'Omitido')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[Optional()])
    submit = SubmitField('Guardar Punto de Control')

class CAPAForm(FlaskForm):
    id = HiddenField()
    # capa_number se podría generar automáticamente
    capa_type = SelectField('Tipo de CAPA', choices=[
        ('corrective', 'Correctiva'),
        ('preventive', 'Preventiva')
    ], validators=[DataRequired()])
    # Campos para la fuente (NonConformity, AuditFinding, etc.) - similar a referencia en Inspección
    source_type = SelectField('Fuente', choices=[
         ('', 'Seleccionar...'),
         ('non_conformity', 'No Conformidad'),
         ('audit_finding', 'Hallazgo de Auditoría'),
         ('customer_feedback', 'Feedback de Cliente'),
         ('other', 'Otro')
    ], validators=[Optional()])
    source_id = IntegerField('ID de Fuente', validators=[Optional()]) # Podría ser QuerySelectField o manejarse con JS
    description = TextAreaField('Descripción del Problema/Hallazgo', validators=[DataRequired()])
    root_cause = TextAreaField('Causa Raíz', validators=[Optional()])
    proposed_action = TextAreaField('Acción Propuesta', validators=[DataRequired()])
    implemented_action = TextAreaField('Acción Implementada', validators=[Optional()])
    status = SelectField('Estado', choices=[
        ('open', 'Abierta'),
        ('in_progress', 'En Progreso'),
        ('implemented', 'Implementada'),
        ('verified', 'Verificada'),
        ('closed', 'Cerrada')
    ], validators=[DataRequired()])
    assigned_to = QuerySelectField('Asignado A', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    due_date = DateTimeField('Fecha Límite', format='%Y-%m-%d %H:%M', validators=[Optional()])
    completion_date = DateTimeField('Fecha de Implementación', format='%Y-%m-%d %H:%M', validators=[Optional()])
    verification_method = TextAreaField('Método de Verificación', validators=[Optional()])
    verified_by = QuerySelectField('Verificada Por', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    verification_date = DateTimeField('Fecha de Verificación', format='%Y-%m-%d %H:%M', validators=[Optional()])
    effectiveness_status = SelectField('Efectividad', choices=[
        ('', 'Seleccionar...'),
        ('effective', 'Efectiva'),
        ('not_effective', 'No Efectiva')
    ], validators=[Optional()])
    notes = TextAreaField('Notas Adicionales', validators=[Optional()])
    submit = SubmitField('Guardar CAPA')

class QualityCertificateForm(FlaskForm):
    id = HiddenField()
    # certificate_number se podría generar automáticamente
    certificate_type = SelectField('Tipo de Certificado', choices=[
        ('', 'Seleccionar...'),
        ('material', 'Material'),
        ('product', 'Producto'),
        ('process', 'Proceso'),
        ('system', 'Sistema')
    ], validators=[Optional()])
    reference_type = SelectField('Tipo de Referencia', choices=[
        ('', 'Seleccionar...'),
        ('material', 'Material'),
        ('product', 'Producto'),
        ('supplier', 'Proveedor')
    ], validators=[Optional()])
    reference_id = IntegerField('ID de Referencia', validators=[Optional()]) # Podría ser QuerySelectField o manejarse con JS
    issue_date = DateTimeField('Fecha de Emisión', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    expiry_date = DateTimeField('Fecha de Vencimiento', format='%Y-%m-%d %H:%M', validators=[Optional()])
    issued_by = StringField('Emitido Por', validators=[Optional(), Length(max=100)])
    certificate_file = FileField('Archivo de Certificado', validators=[FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Solo se permiten archivos PDF, JPG, JPEG o PNG!')]) # FileRequired solo al crear
    notes = TextAreaField('Notas', validators=[Optional()])
    # created_by y created_at se llenan automáticamente
    submit = SubmitField('Guardar Certificado')

class QualityDocumentForm(FlaskForm):
    id = HiddenField()
    document_code = StringField('Código del Documento', validators=[DataRequired(), Length(max=50)]) # Validar unicidad en la ruta
    title = StringField('Título', validators=[DataRequired(), Length(max=255)])
    version = StringField('Versión', validators=[Optional(), Length(max=20)], default='1.0')
    document_type = SelectField('Tipo de Documento', choices=[
        ('', 'Seleccionar...'),
        ('procedure', 'Procedimiento'),
        ('manual', 'Manual'),
        ('policy', 'Política'),
        ('instruction', 'Instrucción'),
        ('form', 'Formato'),
        ('other', 'Otro')
    ], validators=[Optional()])
    issue_date = DateTimeField('Fecha de Emisión', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    revision_date = DateTimeField('Fecha de Revisión', format='%Y-%m-%d %H:%M', validators=[Optional()])
    status = SelectField('Estado', choices=[
        ('active', 'Activo'),
        ('obsolete', 'Obsoleto')
    ], validators=[DataRequired()])
    document_file = FileField('Archivo de Documento', validators=[FileAllowed(['pdf', 'doc', 'docx', 'xlsx', 'pptx'], 'Solo se permiten archivos PDF, DOC, DOCX, XLSX o PPTX!')]) # FileRequired solo al crear
    notes = TextAreaField('Notas', validators=[Optional()])
    # created_by, created_at, updated_at se llenan automáticamente
    submit = SubmitField('Guardar Documento')

class QualityAuditForm(FlaskForm):
    id = HiddenField()
    # audit_number se podría generar automáticamente
    audit_type = SelectField('Tipo de Auditoría', choices=[
        ('internal', 'Interna'),
        ('external', 'Externa')
    ], validators=[DataRequired()])
    scope = TextAreaField('Alcance', validators=[Optional()])
    planned_date = DateTimeField('Fecha Planificada', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    actual_date = DateTimeField('Fecha Real', format='%Y-%m-%d %H:%M', validators=[Optional()])
    lead_auditor = QuerySelectField('Auditor Líder', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    # auditors = TextAreaField('Auditores (Nombres/IDs)', validators=[Optional()]) # Manejar en relación Many-to-Many o campo separado si es lista
    audited_area = StringField('Área Auditada', validators=[Optional(), Length(max=100)])
    status = SelectField('Estado', choices=[
        ('planned', 'Planificada'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[Optional()])
    # created_by, created_at, updated_at se llenan automáticamente
    submit = SubmitField('Guardar Auditoría')

class QualityAuditFindingForm(FlaskForm):
    id = HiddenField()
    audit_id = HiddenField() # Para relacionar con la auditoría padre
    finding_type = SelectField('Tipo de Hallazgo', choices=[
        ('conformity', 'Conformidad'),
        ('non_conformity', 'No Conformidad'),
        ('observation', 'Observación')
    ], validators=[DataRequired()])
    severity = SelectField('Severidad', choices=[
        ('', 'Seleccionar...'),
        ('minor', 'Menor'),
        ('major', 'Mayor'),
        ('critical', 'Crítica')
    ], validators=[Optional()])
    clause = StringField('Cláusula de Norma', validators=[Optional(), Length(max=50)])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    evidence = TextAreaField('Evidencia', validators=[Optional()])
    # Campos para acciones correctivas/preventivas si no se manejan con CAPA separada
    # corrective_action = TextAreaField('Acción Correctiva', validators=[Optional()])
    # preventive_action = TextAreaField('Acción Preventiva', validators=[Optional()])
    status = SelectField('Estado', choices=[
        ('open', 'Abierto'),
        ('in_progress', 'En Progreso'),
        ('closed', 'Cerrado')
    ], validators=[DataRequired()])
    assigned_to = QuerySelectField('Asignado A', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    due_date = DateTimeField('Fecha Límite', format='%Y-%m-%d %H:%M', validators=[Optional()])
    completion_date = DateTimeField('Fecha de Cierre', format='%Y-%m-%d %H:%M', validators=[Optional()])
    verification_date = DateTimeField('Fecha de Verificación', format='%Y-%m-%d %H:%M', validators=[Optional()])
    verified_by = QuerySelectField('Verificado Por', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    notes = TextAreaField('Notas Adicionales', validators=[Optional()])
    # created_at, updated_at se llenan automáticamente
    submit = SubmitField('Guardar Hallazgo')

class QualityNonConformityForm(FlaskForm):
    id = HiddenField()
    # Referencia a Inspección o Auditoría
    inspection = QuerySelectField('Inspección Relacionada', query_factory=get_inspections, allow_blank=True, get_label='inspection_number', validators=[Optional()])
    audit = QuerySelectField('Auditoría Relacionada', query_factory=get_audits, allow_blank=True, get_label='audit_number', validators=[Optional()])
    severity = SelectField('Severidad', choices=[
        ('minor', 'Menor'),
        ('major', 'Mayor'),
        ('critical', 'Crítica')
    ], validators=[DataRequired()])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    # Campos para acciones correctivas/preventivas si no se manejan con CAPA separada
    # root_cause = TextAreaField('Causa Raíz', validators=[Optional()])
    # corrective_action = TextAreaField('Acción Correctiva', validators=[Optional()])
    # preventive_action = TextAreaField('Acción Preventiva', validators=[Optional()])
    status = SelectField('Estado', choices=[
        ('open', 'Abierta'),
        ('in_progress', 'En Progreso'),
        ('implemented', 'Implementada'),
        ('verified', 'Verificada'),
        ('closed', 'Cerrada')
    ], validators=[DataRequired()])
    assigned_to = QuerySelectField('Asignado A', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    due_date = DateTimeField('Fecha Límite', format='%Y-%m-%d %H:%M', validators=[Optional()])
    completion_date = DateTimeField('Fecha de Cierre', format='%Y-%m-%d %H:%M', validators=[Optional()])
    verified_by = QuerySelectField('Verificada Por', query_factory=get_users, allow_blank=True, get_label='username', validators=[Optional()])
    verification_date = DateTimeField('Fecha de Verificación', format='%Y-%m-%d %H:%M', validators=[Optional()])
    notes = TextAreaField('Notas Adicionales', validators=[Optional()])
    # created_by, created_at, updated_at se llenan automáticamente
    submit = SubmitField('Guardar No Conformidad') 