import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app # Importar current_app
from flask_login import login_required, current_user
from app import db
from models.all_models import QualityInspection, User, QualityCheckpoint, QualityNonConformity, CAPA, QualityDocument, QualityAudit, QualityAuditFinding, QualityCertificate # Importar modelos necesarios
from app.forms.qm import QualityInspectionForm, QualityCheckpointForm, QualityNonConformityForm, CAPAForm, QualityDocumentForm, QualityAuditForm, QualityAuditFindingForm, QualityCertificateForm # Importar formularios
from datetime import datetime
from sqlalchemy.orm import joinedload # Importar joinedload para cargar relaciones

qm = Blueprint('qm', __name__, url_prefix='/qm')

# --- Función auxiliar para guardar archivos de forma segura ---
def save_uploaded_file(file, upload_folder):
    # Verificar si el archivo existe y no está vacío
    if file and file.filename:
        # Asegurar el nombre del archivo
        filename = secure_filename(file.filename)
        # Crear la ruta completa al archivo
        file_path = os.path.join(current_app.root_path, upload_folder, filename)
        
        # Asegurar que el directorio de subida existe
        os.makedirs(os.path.join(current_app.root_path, upload_folder), exist_ok=True)
        
        # Guardar el archivo
        file.save(file_path)
        
        # Devolver la ruta relativa o el nombre del archivo para almacenar en la DB
        # Por ahora, guardaremos la ruta relativa desde el root_path de la app
        return os.path.join(upload_folder, filename)
    return None

# --- Función auxiliar para eliminar archivos ---
def delete_uploaded_file(file_path):
    if file_path:
        full_path = os.path.join(current_app.root_path, file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                return True
            except OSError as e:
                current_app.logger.error(f"Error eliminando archivo {full_path}: {e}")
                return False
    return False

# --- Rutas para Inspecciones de Calidad ---

# Ruta para listar inspecciones de calidad
@qm.route('/inspections')
@login_required
def list_inspections():
    # Obtener todas las inspecciones de calidad, cargando el inspector y el creador si es necesario para la visualización
    inspections = QualityInspection.query.options(joinedload(QualityInspection.inspector), joinedload(QualityInspection.creator)).all() # TODO: Considerar paginación
    return render_template('qm/list_inspections.html', inspections=inspections)

# Ruta para añadir una nueva inspección de calidad
@qm.route('/inspections/new', methods=['GET', 'POST'])
@login_required
def add_inspection():
    form = QualityInspectionForm() # Crear instancia del formulario

    # Llenar el campo inspector si el usuario actual es un inspector (opcional, lógica de negocio)
    # if current_user.has_role('inspector'):
    #     form.inspector.data = current_user

    if form.validate_on_submit():
        # TODO: Generar inspection_number automáticamente
        new_inspection = QualityInspection(
            # inspection_number=..., # Asignar número generado
            inspection_type=form.inspection_type.data,
            status=form.status.data,
            # reference_type=form.reference_type.data, # Manejar campos de referencia si se añaden al form
            # reference_id=form.reference_id.data,
            inspection_date=form.inspection_date.data,
            inspector=form.inspector.data, # Asigna el objeto User si se seleccionó
            result=form.result.data,
            notes=form.notes.data,
            created_by=current_user.id # Asignar usuario creador automáticamente
        )
        db.session.add(new_inspection)
        db.session.commit()
        flash('Inspección de calidad creada exitosamente!', 'success')
        # Redirigir a la página de detalle de la inspección para añadir checkpoints
        return redirect(url_for('qm.view_inspection', id=new_inspection.id))

    return render_template('qm/add_edit_inspection.html', title='Añadir Nueva Inspección', form=form)

# Ruta para ver detalles de una inspección de calidad
@qm.route('/inspections/<int:id>')
@login_required
def view_inspection(id):
    # Obtener la inspección por ID o 404, cargando relaciones (inspector, creator, checkpoints, non_conformities)
    inspection = QualityInspection.query.options(
        joinedload(QualityInspection.inspector),
        joinedload(QualityInspection.creator),
        joinedload(QualityInspection.checkpoints),
        joinedload(QualityInspection.non_conformities) # Cargar no conformidades relacionadas
    ).get_or_404(id)

    add_checkpoint_form = QualityCheckpointForm() # Formulario para añadir checkpoints
    add_nonconformity_form = QualityNonConformityForm() # Formulario para añadir no conformidades
    # TODO: Pasar formularios para editar checkpoints/non-conformities/CAPA si se hace desde esta vista

    return render_template('qm/view_inspection.html', 
        inspection=inspection,
        add_checkpoint_form=add_checkpoint_form,
        add_nonconformity_form=add_nonconformity_form # Pasar el formulario
    )

# Ruta para editar una inspección de calidad existente
@qm.route('/inspections/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_inspection(id):
    inspection = QualityInspection.query.get_or_404(id) # Obtener inspección o 404
    form = QualityInspectionForm(obj=inspection) # Precargar formulario

    if form.validate_on_submit():
        # Actualizar datos de la inspección
        inspection.inspection_type = form.inspection_type.data
        inspection.status = form.status.data
        # inspection.reference_type = form.reference_type.data # Manejar campos de referencia
        # inspection.reference_id = form.reference_id.data,
        inspection.inspection_date = form.inspection_date.data
        inspection.inspector = form.inspector.data # Asigna el objeto User
        inspection.result = form.result.data
        inspection.notes = form.notes.data
        # updated_at se actualiza automáticamente por el modelo

        db.session.commit()
        flash('Inspección de calidad actualizada exitosamente!', 'success')
        return redirect(url_for('qm.view_inspection', id=inspection.id))

    return render_template('qm/add_edit_inspection.html', title='Editar Inspección', form=form)

# Ruta para eliminar una inspección de calidad (solo POST)
@qm.route('/inspections/delete/<int:id>', methods=['POST'])
@login_required
def delete_inspection(id):
    inspection = QualityInspection.query.get_or_404(id)
    db.session.delete(inspection)
    db.session.commit()
    flash('Inspección de calidad eliminada exitosamente!', 'success')
    return redirect(url_for('qm.list_inspections'))

# --- Rutas para Puntos de Control (Checkpoints) ---

# Ruta para añadir un punto de control a una inspección
@qm.route('/inspections/<int:inspection_id>/checkpoints/new', methods=['POST'])
@login_required
def add_checkpoint(inspection_id):
    inspection = QualityInspection.query.get_or_404(inspection_id)
    form = QualityCheckpointForm()

    # Si el formulario es válido, guardar el checkpoint
    if form.validate_on_submit():
        new_checkpoint = QualityCheckpoint(
            inspection_id=inspection.id,
            checkpoint_type=form.checkpoint_type.data,
            description=form.description.data,
            requirement=form.requirement.data,
            result_type=form.result_type.data,
            result=form.result.data,
            measurement_value=form.measurement_value.data,
            measurement_unit=form.measurement_unit.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(new_checkpoint)
        db.session.commit()
        flash('Punto de control añadido exitosamente!', 'success')
        return redirect(url_for('qm.view_inspection', id=inspection.id))
    else:
        # Si hay errores de validación, flashear los errores y redirigir de vuelta a la vista de inspección
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
        # Redirigir de vuelta a la página de inspección, posiblemente con un indicador para reabrir el modal
        return redirect(url_for('qm.view_inspection', id=inspection.id, modal='addCheckpointModal'))


# Ruta para editar un punto de control
@qm.route('/checkpoints/edit/<int:checkpoint_id>', methods=['POST'])
@login_required
def edit_checkpoint(checkpoint_id):
    checkpoint = QualityCheckpoint.query.get_or_404(checkpoint_id)
    form = QualityCheckpointForm(obj=checkpoint)

    # Si el formulario es válido, actualizar el checkpoint
    if form.validate_on_submit():
        form.populate_obj(checkpoint) # Actualiza el objeto checkpoint con los datos del formulario
        db.session.commit()
        flash('Punto de control actualizado exitosamente!', 'success')
        return redirect(url_for('qm.view_inspection', id=checkpoint.inspection_id))
    else:
         # Si hay errores de validación, flashear los errores y redirigir de vuelta a la vista de inspección
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
        # Redirigir de vuelta a la página de inspección, con indicador y ID del checkpoint para reabrir modal de edición
        return redirect(url_for('qm.view_inspection', id=checkpoint.inspection_id, modal=f'editCheckpointModal{checkpoint.id}'))


# Ruta para eliminar un punto de control (solo POST)
@qm.route('/checkpoints/delete/<int:checkpoint_id>', methods=['POST'])
@login_required
def delete_checkpoint(checkpoint_id):
    checkpoint = QualityCheckpoint.query.get_or_404(checkpoint_id)
    inspection_id = checkpoint.inspection_id
    db.session.delete(checkpoint)
    db.session.commit()
    flash('Punto de control eliminado exitosamente!', 'success')
    return redirect(url_for('qm.view_inspection', id=inspection_id))

# --- Rutas para No Conformidades ---

# Ruta para listar no conformidades
@qm.route('/non_conformities')
@login_required
def list_non_conformities():
    # Obtener todas las no conformidades, cargando relaciones si es necesario
    non_conformities = QualityNonConformity.query.options(joinedload(QualityNonConformity.assigned_to), joinedload(QualityNonConformity.verified_by), joinedload(QualityNonConformity.creator)).all() # TODO: Considerar paginación
    return render_template('qm/list_non_conformities.html', non_conformities=non_conformities)

# Ruta para añadir una nueva no conformidad
@qm.route('/non_conformities/new', methods=['GET', 'POST'])
@login_required
def add_non_conformity():
    form = QualityNonConformityForm() # Crear instancia del formulario

    if form.validate_on_submit():
        new_nc = QualityNonConformity(
            severity=form.severity.data,
            description=form.description.data,
            root_cause=form.root_cause.data,
            corrective_action=form.corrective_action.data,
            preventive_action=form.preventive_action.data,
            status=form.status.data,
            assigned_to=form.assigned_to.data, # Asigna el objeto User
            due_date=form.due_date.data,
            completion_date=form.completion_date.data,
            verified_by=form.verified_by.data, # Asigna el objeto User
            verification_date=form.verification_date.data,
            notes=form.notes.data,
            # inspection=form.inspection.data, # Manejar relación con Inspección si está en el form
            # audit=form.audit.data, # Manejar relación con Auditoría si está en el form
            created_by=current_user.id # Asignar usuario creador automáticamente
        )
        db.session.add(new_nc)
        db.session.commit()
        flash('No Conformidad creada exitosamente!', 'success')
        return redirect(url_for('qm.view_non_conformity', id=new_nc.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_non_conformity.html', title='Añadir Nueva No Conformidad', form=form)

# Ruta para ver detalles de una no conformidad
@qm.route('/non_conformities/<int:id>')
@login_required
def view_non_conformity(id):
    # Obtener la no conformidad por ID o 404, cargando relaciones si es necesario
    non_conformity = QualityNonConformity.query.options(
        joinedload(QualityNonConformity.assigned_to),
        joinedload(QualityNonConformity.verified_by),
        joinedload(QualityNonConformity.creator)
        # TODO: Cargar relaciones con Inspection y Audit si existen
    ).get_or_404(id)
    return render_template('qm/view_non_conformity.html', non_conformity=non_conformity)

# Ruta para editar una no conformidad existente
@qm.route('/non_conformities/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_non_conformity(id):
    non_conformity = QualityNonConformity.query.get_or_404(id) # Obtener no conformidad o 404
    form = QualityNonConformityForm(obj=non_conformity) # Precargar formulario

    if form.validate_on_submit():
        form.populate_obj(non_conformity) # Actualizar objeto con datos del formulario
        # updated_at se actualiza automáticamente por el modelo

        db.session.commit()
        flash('No Conformidad actualizada exitosamente!', 'success')
        return redirect(url_for('qm.view_non_conformity', id=non_conformity.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_non_conformity.html', title='Editar No Conformidad', form=form)

# Ruta para eliminar una no conformidad (solo POST)
@qm.route('/non_conformities/delete/<int:id>', methods=['POST'])
@login_required
def delete_non_conformity(id):
    non_conformity = QualityNonConformity.query.get_or_404(id)
    db.session.delete(non_conformity)
    db.session.commit()
    flash('No Conformidad eliminada exitosamente!', 'success')
    return redirect(url_for('qm.list_non_conformities'))

# --- Rutas para CAPA ---

# Ruta para listar CAPAs
@qm.route('/capas')
@login_required
def list_capas():
    # Obtener todas las CAPAs, cargando relaciones si es necesario
    capas = CAPA.query.options(joinedload(CAPA.assigned_to), joinedload(CAPA.verified_by), joinedload(CAPA.creator)).all() # TODO: Considerar paginación
    return render_template('qm/list_capas.html', capas=capas)

# Ruta para añadir una nueva CAPA
@qm.route('/capas/new', methods=['GET', 'POST'])
@login_required
def add_capa():
    form = CAPAForm() # Crear instancia del formulario

    if form.validate_on_submit():
        new_capa = CAPA(
            capa_type=form.capa_type.data,
            source_type=form.source_type.data,
            source_id=form.source_id.data,
            description=form.description.data,
            root_cause=form.root_cause.data,
            proposed_action=form.proposed_action.data,
            implemented_action=form.implemented_action.data,
            status=form.status.data,
            assigned_to=form.assigned_to.data, # Asigna el objeto User
            due_date=form.due_date.data,
            completion_date=form.completion_date.data,
            verification_method=form.verification_method.data,
            verified_by=form.verified_by.data, # Asigna el objeto User
            verification_date=form.verification_date.data,
            effectiveness_status=form.effectiveness_status.data,
            notes=form.notes.data,
            created_by=current_user.id # Asignar usuario creador automáticamente
        )
        db.session.add(new_capa)
        db.session.commit()
        flash('CAPA creada exitosamente!', 'success')
        return redirect(url_for('qm.view_capa', id=new_capa.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_capa.html', title='Añadir Nueva CAPA', form=form)

# Ruta para ver detalles de una CAPA
@qm.route('/capas/<int:id>')
@login_required
def view_capa(id):
    # Obtener la CAPA por ID o 404, cargando relaciones si es necesario
    capa = CAPA.query.options(
        joinedload(CAPA.assigned_to),
        joinedload(CAPA.verified_by),
        joinedload(CAPA.creator)
        # TODO: Cargar relaciones con source_type (NonConformity, AuditFinding, etc.)
    ).get_or_404(id)
    return render_template('qm/view_capa.html', capa=capa)

# Ruta para editar una CAPA existente
@qm.route('/capas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_capa(id):
    capa = CAPA.query.get_or_404(id) # Obtener CAPA o 404
    form = CAPAForm(obj=capa) # Precargar formulario

    if form.validate_on_submit():
        form.populate_obj(capa) # Actualizar objeto con datos del formulario
        # updated_at se actualiza automáticamente por el modelo

        db.session.commit()
        flash('CAPA actualizada exitosamente!', 'success')
        return redirect(url_for('qm.view_capa', id=capa.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_capa.html', title='Editar CAPA', form=form)

# Ruta para eliminar una CAPA (solo POST)
@qm.route('/capas/delete/<int:id>', methods=['POST'])
@login_required
def delete_capa(id):
    capa = CAPA.query.get_or_404(id)
    db.session.delete(capa)
    db.session.commit()
    flash('CAPA eliminada exitosamente!', 'success')
    return redirect(url_for('qm.list_capas'))

# --- Rutas para Documentos de Calidad ---

# Ruta para listar documentos de calidad
@qm.route('/documents')
@login_required
def list_documents():
    # Obtener todos los documentos, cargando creador si es necesario
    documents = QualityDocument.query.options(joinedload(QualityDocument.creator)).all() # TODO: Considerar paginación
    return render_template('qm/list_documents.html', documents=documents)

# Ruta para añadir un nuevo documento de calidad
@qm.route('/documents/new', methods=['GET', 'POST'])
@login_required
def add_document():
    form = QualityDocumentForm() # Crear instancia del formulario

    if form.validate_on_submit():
        # TODO: Validar unicidad del document_code
        
        file_path = None
        if form.document_file.data:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') # Usar una carpeta de subida configurable
            file_path = save_uploaded_file(form.document_file.data, upload_folder)
            if file_path is None:
                flash('Error al subir el archivo del documento.', 'danger')
                return redirect(url_for('qm.add_document')) # Redirigir de vuelta con el formulario

        # TODO: file_path es campo obligatorio en el formulario, ajustar lógica si no se sube archivo en add

        new_document = QualityDocument(
            document_code=form.document_code.data,
            title=form.title.data,
            version=form.version.data,
            document_type=form.document_type.data,
            issue_date=form.issue_date.data,
            revision_date=form.revision_date.data,
            status=form.status.data,
            file_path=file_path, # Guardar la ruta del archivo
            notes=form.notes.data,
            created_by=current_user.id # Asignar usuario creador automáticamente
        )
        db.session.add(new_document)
        db.session.commit()
        flash('Documento de calidad creado exitosamente!', 'success')
        return redirect(url_for('qm.view_document', id=new_document.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_document.html', title='Añadir Nuevo Documento', form=form)

# Ruta para ver detalles de un documento de calidad
@qm.route('/documents/<int:id>')
@login_required
def view_document(id):
    # Obtener el documento por ID o 404, cargando relaciones si es necesario
    document = QualityDocument.query.options(joinedload(QualityDocument.creator)).get_or_404(id)
    # TODO: Enlace para descargar el archivo
    return render_template('qm/view_document.html', document=document)

# Ruta para editar un documento de calidad existente
@qm.route('/documents/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_document(id):
    document = QualityDocument.query.get_or_404(id) # Obtener documento o 404
    form = QualityDocumentForm(obj=document) # Precargar formulario
    
    # Si se está editando, eliminar el validador FileRequired para que la edición sin subir archivo nuevo sea posible
    if request.method == 'GET':
         # Encontrar el validador FileRequired en form.document_file.validators y removerlo
         original_validators = form.document_file.validators
         form.document_file.validators = [v for v in original_validators if not isinstance(v, FileRequired)]
         
    if form.validate_on_submit():
        file_path = document.file_path # Mantener el archivo existente por defecto
        if form.document_file.data and form.document_file.data.filename:
            # Si se sube un nuevo archivo, primero eliminar el anterior si existe
            if document.file_path:
                delete_uploaded_file(document.file_path)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            file_path = save_uploaded_file(form.document_file.data, upload_folder)
            if file_path is None:
                flash('Error al subir el nuevo archivo del documento.', 'danger')
                 # TODO: Considerar si redirigir o renderizar el template con errores
                return redirect(url_for('qm.edit_document', id=document.id)) 
        elif request.method == 'POST' and not form.document_file.data and document.file_path:
            # Si no se subió un nuevo archivo pero ya existía uno, mantener la ruta existente
            pass # file_path ya tiene la ruta existente
        elif request.method == 'POST' and not form.document_file.data and not document.file_path:
            # Si no se subió archivo y no existía uno, asegurar que file_path sea None o cadena vacía
            file_path = None # O manejar según si el campo es obligatorio o no en el modelo

        # Actualizar objeto con datos del formulario
        document.document_code = form.document_code.data
        document.title = form.title.data
        document.version = form.version.data
        document.document_type = form.document_type.data
        document.issue_date = form.issue_date.data
        document.revision_date = form.revision_date.data
        document.status = form.status.data
        document.file_path = file_path # Actualizar con la nueva ruta o mantener la existente
        document.notes = form.notes.data
        # updated_at se actualiza automáticamente por el modelo

        db.session.commit()
        flash('Documento de calidad actualizado exitosamente!', 'success')
        return redirect(url_for('qm.view_document', id=document.id)) # Redirigir a la vista de detalle

    # Si es GET, la plantilla renderizará el formulario con los datos existentes
    return render_template('qm/add_edit_document.html', title='Editar Documento', form=form)

# Ruta para eliminar un documento de calidad (solo POST)
@qm.route('/documents/delete/<int:id>', methods=['POST'])
@login_required
def delete_document(id):
    document = QualityDocument.query.get_or_404(id)
    # Eliminar el archivo físico asociado de forma segura antes de eliminar el registro de la DB
    if document.file_path:
        delete_uploaded_file(document.file_path)
        
    db.session.delete(document)
    db.session.commit()
    flash('Documento de calidad eliminado exitosamente!', 'success')
    return redirect(url_for('qm.list_documents'))

# --- Rutas para Auditorías ---

# Ruta para listar auditorías
@qm.route('/audits')
@login_required
def list_audits():
    # Obtener todas las auditorías, cargando relaciones si es necesario
    audits = QualityAudit.query.options(joinedload(QualityAudit.lead_auditor), joinedload(QualityAudit.creator)).all() # TODO: Considerar paginación
    return render_template('qm/list_audits.html', audits=audits)

# Ruta para añadir una nueva auditoría
@qm.route('/audits/new', methods=['GET', 'POST'])
@login_required
def add_audit():
    form = QualityAuditForm() # Crear instancia del formulario

    if form.validate_on_submit():
        # TODO: Generar audit_number automáticamente
        new_audit = QualityAudit(
            # audit_number=..., # Asignar número generado
            audit_type=form.audit_type.data,
            scope=form.scope.data,
            planned_date=form.planned_date.data,
            executed_date=form.executed_date.data,
            status=form.status.data,
            lead_auditor=form.lead_auditor.data, # Asigna el objeto User
            audited_area=form.audited_area.data,
            report_date=form.report_date.data,
            notes=form.notes.data,
            created_by=current_user.id # Asignar usuario creador automáticamente
        )
        db.session.add(new_audit)
        db.session.commit()
        flash('Auditoría creada exitosamente!', 'success')
        return redirect(url_for('qm.view_audit', id=new_audit.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_audit.html', title='Añadir Nueva Auditoría', form=form)

# Ruta para ver detalles de una auditoría
@qm.route('/audits/<int:id>')
@login_required
def view_audit(id):
    # Obtener la auditoría por ID o 404, cargando relaciones (lead_auditor, creator, findings)
    audit = QualityAudit.query.options(
        joinedload(QualityAudit.lead_auditor),
        joinedload(QualityAudit.creator),
        joinedload(QualityAudit.findings) # Cargar hallazgos relacionados
    ).get_or_404(id)

    add_finding_form = QualityAuditFindingForm() # Formulario para añadir hallazgos
    # TODO: Pasar formularios para editar findings si se hace desde esta vista

    return render_template('qm/view_audit.html', 
        audit=audit,
        add_finding_form=add_finding_form # Pasar el formulario
    )

# Ruta para editar una auditoría existente
@qm.route('/audits/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_audit(id):
    audit = QualityAudit.query.get_or_404(id) # Obtener auditoría o 404
    form = QualityAuditForm(obj=audit) # Precargar formulario

    if form.validate_on_submit():
        form.populate_obj(audit) # Actualizar objeto con datos del formulario
        # updated_at se actualiza automáticamente por el modelo

        db.session.commit()
        flash('Auditoría actualizada exitosamente!', 'success')
        return redirect(url_for('qm.view_audit', id=audit.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_audit.html', title='Editar Auditoría', form=form)

# Ruta para eliminar una auditoría (solo POST)
@qm.route('/audits/delete/<int:id>', methods=['POST'])
@login_required
def delete_audit(id):
    audit = QualityAudit.query.get_or_404(id)
    db.session.delete(audit) # Esto debería eliminar también findings por cascade
    db.session.commit()
    flash('Auditoría eliminada exitosamente!', 'success')
    return redirect(url_for('qm.list_audits'))

# --- Rutas para Hallazgos de Auditoría ---

# Ruta para añadir un hallazgo a una auditoría
@qm.route('/audits/<int:audit_id>/findings/new', methods=['POST'])
@login_required
def add_audit_finding(audit_id):
    audit = QualityAudit.query.get_or_404(audit_id)
    form = QualityAuditFindingForm() # Usamos el mismo formulario que pasamos a la plantilla

    # Si el formulario es válido, guardar el hallazgo
    if form.validate_on_submit():
        new_finding = QualityAuditFinding(
            audit_id=audit.id,
            finding_type=form.finding_type.data,
            severity=form.severity.data,
            clause=form.clause.data,
            description=form.description.data,
            evidence=form.evidence.data,
            status=form.status.data,
            assigned_to=form.assigned_to.data, # Asigna el objeto User
            due_date=form.due_date.data,
            completion_date=form.completion_date.data,
            verified_by=form.verified_by.data, # Asigna el objeto User
            verification_date=form.verification_date.data,
            notes=form.notes.data
        )
        db.session.add(new_finding)
        db.session.commit()
        flash('Hallazgo de auditoría añadido exitosamente!', 'success')
        return redirect(url_for('qm.view_audit', id=audit.id))
    else:
        # Si hay errores de validación, flashear los errores y redirigir de vuelta a la vista de auditoría
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
        # Redirigir de vuelta a la página de auditoría, con indicador para reabrir el modal
        return redirect(url_for('qm.view_audit', id=audit.id, modal='addFindingModal'))

# Ruta para editar un hallazgo de auditoría
@qm.route('/audit_findings/edit/<int:finding_id>', methods=['POST'])
@login_required
def edit_audit_finding(finding_id):
    finding = QualityAuditFinding.query.get_or_404(finding_id)
    form = QualityAuditFindingForm(obj=finding) # Intentamos precargar el formulario con el objeto existente

    # Si el formulario es válido, actualizar el hallazgo
    if form.validate_on_submit():
        form.populate_obj(finding) # Actualiza el objeto finding con los datos del formulario
        db.session.commit()
        flash('Hallazgo de auditoría actualizado exitosamente!', 'success')
        return redirect(url_for('qm.view_audit', id=finding.audit_id)) # Redirigir de vuelta a la auditoría principal
    else:
         # Si hay errores de validación, flashear los errores y redirigir de vuelta a la vista de auditoría
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
        # Redirigir de vuelta a la página de auditoría, con indicador y ID del finding para reabrir modal de edición
        return redirect(url_for('qm.view_audit', id=finding.audit_id, modal=f'editFindingModal{finding.id}'))

# Ruta para eliminar un hallazgo de auditoría (solo POST)
@qm.route('/audit_findings/delete/<int:finding_id>', methods=['POST'])
@login_required
def delete_audit_finding(finding_id):
    finding = QualityAuditFinding.query.get_or_404(finding_id)
    audit_id = finding.audit_id
    db.session.delete(finding)
    db.session.commit()
    flash('Hallazgo de auditoría eliminado exitosamente!', 'success')
    return redirect(url_for('qm.view_audit', id=audit_id))

# --- Rutas para Certificados de Calidad ---

# Ruta para listar certificados de calidad
@qm.route('/certificates')
@login_required
def list_certificates():
    # Obtener todos los certificados, cargando relaciones si es necesario
    certificates = QualityCertificate.query.options(joinedload(QualityCertificate.issued_by), joinedload(QualityCertificate.certified_party), joinedload(QualityCertificate.creator)).all() # TODO: Considerar paginación
    return render_template('qm/list_certificates.html', certificates=certificates)

# Ruta para añadir un nuevo certificado de calidad
@qm.route('/certificates/new', methods=['GET', 'POST'])
@login_required
def add_certificate():
    form = QualityCertificateForm() # Crear instancia del formulario

    if form.validate_on_submit():
        # TODO: Validar unicidad del certificate_number

        file_path = None
        if form.certificate_file.data:
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') # Usar una carpeta de subida configurable
            file_path = save_uploaded_file(form.certificate_file.data, upload_folder)
            if file_path is None:
                flash('Error al subir el archivo del certificado.', 'danger')
                return redirect(url_for('qm.add_certificate')) # Redirigir de vuelta con el formulario

        new_certificate = QualityCertificate(
            certificate_number=form.certificate_number.data,
            title=form.title.data,
            standard_specification=form.standard_specification.data,
            issue_date=form.issue_date.data,
            expiry_date=form.expiry_date.data,
            status=form.status.data,
            issued_by=form.issued_by.data, # Asigna el objeto User o Party
            certified_party=form.certified_party.data, # Asigna el objeto Party
            file_path=file_path, # Guardar la ruta del archivo
            notes=form.notes.data,
            created_by=current_user.id # Asignar usuario creador automáticamente
        )
        db.session.add(new_certificate)
        db.session.commit()
        flash('Certificado de calidad creado exitosamente!', 'success')
        return redirect(url_for('qm.view_certificate', id=new_certificate.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_certificate.html', title='Añadir Nuevo Certificado', form=form)

# Ruta para ver detalles de un certificado de calidad
@qm.route('/certificates/<int:id>')
@login_required
def view_certificate(id):
    # Obtener el certificado por ID o 404, cargando relaciones si es necesario
    certificate = QualityCertificate.query.options(joinedload(QualityCertificate.issued_by), joinedload(QualityCertificate.certified_party), joinedload(QualityCertificate.creator)).get_or_404(id)
    # TODO: Enlace para descargar el archivo
    return render_template('qm/view_certificate.html', certificate=certificate)

# Ruta para editar un certificado de calidad existente
@qm.route('/certificates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_certificate(id):
    certificate = QualityCertificate.query.get_or_404(id) # Obtener certificado o 404
    form = QualityCertificateForm(obj=certificate) # Precargar formulario

    if form.validate_on_submit():
        # TODO: Manejar la subida de archivos si se selecciona uno nuevo
        file_path = certificate.file_path # Mantener el archivo existente por defecto
        if form.certificate_file.data:
            # Si se sube un nuevo archivo, primero eliminar el anterior si existe
            if certificate.file_path:
                delete_uploaded_file(certificate.file_path)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            file_path = save_uploaded_file(form.certificate_file.data, upload_folder)
            if file_path is None:
                flash('Error al subir el nuevo archivo del certificado.', 'danger')
                 # TODO: Considerar si redirigir o renderizar el template con errores
                return redirect(url_for('qm.edit_certificate', id=certificate.id)) 

        # Actualizar objeto con datos del formulario
        certificate.certificate_number = form.certificate_number.data
        certificate.title = form.title.data
        certificate.standard_specification = form.standard_specification.data
        certificate.issue_date = form.issue_date.data
        certificate.expiry_date = form.expiry_date.data
        certificate.status = form.status.data
        certificate.issued_by = form.issued_by.data
        certificate.certified_party = form.certified_party.data
        certificate.file_path = file_path # Actualizar con la nueva ruta si se subió un archivo
        certificate.notes = form.notes.data
        # updated_at se actualiza automáticamente por el modelo

        db.session.commit()
        flash('Certificado de calidad actualizado exitosamente!', 'success')
        return redirect(url_for('qm.view_certificate', id=certificate.id)) # Redirigir a la vista de detalle

    return render_template('qm/add_edit_certificate.html', title='Editar Certificado', form=form)

# Ruta para eliminar un certificado de calidad (solo POST)
@qm.route('/certificates/delete/<int:id>', methods=['POST'])
@login_required
def delete_certificate(id):
    certificate = QualityCertificate.query.get_or_404(id)
    # Eliminar el archivo físico asociado de forma segura antes de eliminar el registro de la DB
    if certificate.file_path:
        delete_uploaded_file(certificate.file_path)
        
    db.session.delete(certificate)
    db.session.commit()
    flash('Certificado de calidad eliminado exitosamente!', 'success')
    return redirect(url_for('qm.list_certificates')) 