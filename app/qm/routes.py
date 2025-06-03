from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.models.qm import Inspection, Checkpoint, NonConformity, Certificate, Document, Audit, AuditFinding, CAPA
from app.forms.qm import (InspectionForm, CheckpointForm, NonConformityForm, 
                          CertificateForm, DocumentForm, AuditForm, AuditFindingForm, CAPAForm)
from datetime import datetime # Importar datetime
import os # Importar os
from werkzeug.utils import secure_filename # Importar secure_filename
from sqlalchemy import desc # Importar desc para ordenar
# Importar otros modelos si es necesario (ej: Material, ProductionOrder para referencias)
# from app.models.mm import Material, PurchaseOrder
# from app.models.pp import ProductionOrder, Product

qm = Blueprint('qm', __name__, url_prefix='/qm')

# Directorios de subida de archivos
UPLOAD_FOLDER_CERTIFICATES = 'static/uploads/qm/certificates'
UPLOAD_FOLDER_DOCUMENTS = 'static/uploads/qm/documents'

# Asegurarse de que los directorios existen
if not os.path.exists(os.path.join(current_app.root_path, UPLOAD_FOLDER_CERTIFICATES)):
    os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_CERTIFICATES))
if not os.path.exists(os.path.join(current_app.root_path, UPLOAD_FOLDER_DOCUMENTS)):
    os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER_DOCUMENTS))

# --- Rutas para Gestión de Inspecciones ---

@qm.route('/inspections')
@login_required
def list_inspections():
    # Implementar filtros de búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Definir cuántos elementos por página

    # Obtener parámetros de filtro de la URL
    search = request.args.get('search')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')

    query = Inspection.query

    if search:
        # Buscar por número de inspección o ID de referencia
        query = query.filter(
            (Inspection.inspection_number.ilike(f'%{search}%')) |
            (Inspection.reference_id.cast(db.String).ilike(f'%{search}%'))
        )

    if type_filter and type_filter != 'all':
        query = query.filter_by(inspection_type=type_filter)

    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)

    inspections = query.order_by(Inspection.created_at.desc()).paginate(page=page, per_page=per_page)

    return render_template('qm/inspections.html', title='Gestión de Inspecciones', 
                           inspections=inspections, search=search, type=type_filter, status=status_filter)

@qm.route('/inspections/new', methods=['GET', 'POST'])
@login_required
def new_inspection():
    form = InspectionForm()
    if form.validate_on_submit():
        # --- Lógica para generar el número de inspección automáticamente ---
        current_year = datetime.utcnow().year
        prefix = "QM"
        # Buscar la última inspección del año actual para obtener el último número
        last_inspection = Inspection.query.filter(
            Inspection.inspection_number.like(f'{prefix}-{str(current_year)[2:]}-%')
        ).order_by(desc(Inspection.inspection_number)).first()

        sequence_number = 1
        if last_inspection and last_inspection.inspection_number:
            try:
                # Extraer el número secuencial de la cadena (ej: "QM-24-0001" -> 1)
                last_number_str = last_inspection.inspection_number.split('-')[-1]
                sequence_number = int(last_number_str) + 1
            except (ValueError, IndexError):
                # En caso de error al parsear, empezar desde 1 (o manejar el error apropiadamente)
                sequence_number = 1 # Considerar loguear este error

        # Formatear el nuevo número (ej: "QM-24-0002")
        new_inspection_number = f'{prefix}-{str(current_year)[2:]}-{sequence_number:04d}'
        # --- Fin de la lógica de generación de número ---

        inspection = Inspection(
            inspection_number=new_inspection_number, # Usar el número generado
            inspection_type=form.inspection_type.data,
            reference_type=form.reference_type.data if form.reference_type.data != '' else None,
            reference_id=form.reference_id.data if form.reference_id.data != '' else None,
            status=form.status.data,
            due_date=form.due_date.data,
            inspector_id=form.inspector_id.data.id if form.inspector_id.data else None,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(inspection)
        db.session.commit()
        flash('Inspección creada exitosamente!', 'success')
        return redirect(url_for('qm.list_inspections'))
    return render_template('qm/new_inspection.html', title='Nueva Inspección', form=form)

@qm.route('/inspections/<int:id>')
@login_required
def inspection_detail(id):
    inspection = Inspection.query.get_or_404(id)
    # Pasar formularios para modales de añadir/editar puntos de control y no conformidades
    form_new_checkpoint = CheckpointForm()
    form_new_non_conformity = NonConformityForm()
    form_edit_checkpoint = CheckpointForm() # Usar uno solo y llenarlo con JS
    form_edit_non_conformity = NonConformityForm() # Usar uno solo y llenarlo con JS
    form_close_non_conformity = NonConformityForm() # Usar uno solo y llenarlo con JS para cerrar

    return render_template('qm/inspection_detail.html', title=f'Inspección #{inspection.inspection_number}', 
                           inspection=inspection, form_new_checkpoint=form_new_checkpoint, 
                           form_new_non_conformity=form_new_non_conformity,
                           form_edit_checkpoint=form_edit_checkpoint, 
                           form_edit_non_conformity=form_edit_non_conformity,
                           form_close_non_conformity=form_close_non_conformity)

@qm.route('/inspections/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inspection(id):
    inspection = Inspection.query.get_or_404(id)
    form = InspectionForm(obj=inspection) # Pre-pobla el formulario con los datos existentes
    if form.validate_on_submit():
        # Actualizar los campos del objeto inspection con los datos del formulario
        form.populate_obj(inspection)
        # Manejar el campo inspector_id por separado ya que es un QuerySelectField
        inspection.inspector_id = form.inspector_id.data.id if form.inspector_id.data else None
        
        # Actualizar fecha de actualización
        inspection.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Inspección actualizada exitosamente!', 'success')
        return redirect(url_for('qm.inspection_detail', id=inspection.id))
    # Si es GET o el formulario no es válido, renderizar la plantilla con el formulario (pre-llenado en GET)
    return render_template('qm/new_inspection.html', title=f'Editar Inspección #{inspection.inspection_number}', form=form, inspection=inspection)

@qm.route('/inspections/<int:inspection_id>/checkpoints/add', methods=['POST'])
@login_required
def add_checkpoint(inspection_id):
    inspection = Inspection.query.get_or_404(inspection_id)
    form = CheckpointForm()
    if form.validate_on_submit():
        checkpoint = Checkpoint(
            inspection_id=inspection.id,
            description=form.description.data,
            standard=form.standard.data,
            acceptance_criteria=form.acceptance_criteria.data,
            measurement_value=form.measurement_value.data,
            measurement_unit=form.measurement_unit.data,
            status=form.status.data,
            notes=form.notes.data
        )
        db.session.add(checkpoint)
        db.session.commit()
        flash('Punto de control añadido exitosamente!', 'success')
    else:
         for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')
                
    return redirect(url_for('qm.inspection_detail', id=inspection.id))

@qm.route('/checkpoints/<int:id>/edit', methods=['POST'])
@login_required
def edit_checkpoint(id):
    checkpoint = Checkpoint.query.get_or_404(id)
    # Nos aseguramos de que el punto de control pertenece a una inspección (debería ser siempre así)
    if not checkpoint.inspection_id:
         abort(404)

    form = CheckpointForm(obj=checkpoint) # Pre-pobla el formulario con los datos existentes
    if form.validate_on_submit():
        # Actualizar los campos del objeto checkpoint con los datos del formulario
        form.populate_obj(checkpoint)
        
        # Actualizar fecha de actualización
        checkpoint.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Punto de control actualizado exitosamente!', 'success')
    else:
         for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la página de detalle de la inspección
    return redirect(url_for('qm.inspection_detail', id=checkpoint.inspection_id))

@qm.route('/checkpoints/<int:id>/delete', methods=['POST'])
@login_required
def delete_checkpoint(id):
    checkpoint = Checkpoint.query.get_or_404(id)
    inspection_id = checkpoint.inspection_id # Guardar el ID de la inspección antes de eliminar

    # Nos aseguramos de que el punto de control pertenece a una inspección (debería ser siempre así)
    if not inspection_id:
         abort(404)
         
    db.session.delete(checkpoint)
    db.session.commit()
    flash('Punto de control eliminado exitosamente!', 'success')

    # Redirigir de vuelta a la página de detalle de la inspección
    return redirect(url_for('qm.inspection_detail', id=inspection_id))

@qm.route('/inspections/<int:inspection_id>/non_conformities/add', methods=['POST'])
@login_required
def add_non_conformity(inspection_id):
    inspection = Inspection.query.get_or_404(inspection_id)
    form = NonConformityForm()
    if form.validate_on_submit():
        non_conformity = NonConformity(
            inspection_id=inspection.id,
            severity=form.severity.data,
            description=form.description.data,
            root_cause=form.root_cause.data,
            corrective_action=form.corrective_action.data,
            preventive_action=form.preventive_action.data,
            status=form.status.data,
            assigned_to_id=form.assigned_to_id.data.id if form.assigned_to_id.data else None,
            due_date=form.due_date.data,
            notes=form.notes.data,
            created_by=current_user.id # Asignar el usuario actual como creador
        )
        db.session.add(non_conformity)
        db.session.commit()
        flash('No Conformidad registrada exitosamente!', 'success')
    else:
         for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('qm.inspection_detail', id=inspection.id))

@qm.route('/non_conformities/<int:id>/edit', methods=['POST'])
@login_required
def edit_non_conformity(id):
    non_conformity = NonConformity.query.get_or_404(id)
    # Asegurarse de que la NC está ligada a algo (inspección o auditoría)
    if not non_conformity.inspection_id and not non_conformity.audit_id:
        abort(404)

    form = NonConformityForm(obj=non_conformity)
    if form.validate_on_submit():
        form.populate_obj(non_conformity)
        # Manejar el campo assigned_to_id por separado
        non_conformity.assigned_to_id = form.assigned_to_id.data.id if form.assigned_to_id.data else None
        
        non_conformity.updated_at = datetime.utcnow()
        db.session.commit()
        flash('No Conformidad actualizada exitosamente!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la página de detalle correcta (Inspección o Auditoría)
    if non_conformity.inspection_id:
        return redirect(url_for('qm.inspection_detail', id=non_conformity.inspection_id))
    elif non_conformity.audit_id:
        # TODO: Redirigir a la página de detalle de auditoría cuando esté implementada
        flash('Redirección a auditoría no implementada', 'info')
        return redirect(url_for('qm.list_inspections')) # Redirigir a lista de inspecciones temporalmente
    else:
        # Esto no debería ocurrir si la comprobación inicial pasa
        return redirect(url_for('qm.list_inspections'))

@qm.route('/non_conformities/<int:id>/close', methods=['POST'])
@login_required
def close_non_conformity(id):
    non_conformity = NonConformity.query.get_or_404(id)

    # Asegurarse de que la NC está ligada a algo (inspección o auditoría)
    if not non_conformity.inspection_id and not non_conformity.audit_id:
        abort(404)

    form = NonConformityForm(obj=non_conformity) # Usamos el mismo formulario base
    # Validar solo los campos necesarios para el cierre si es diferente del formulario de edición completo
    # Por ahora, validaremos el formulario completo como está definido.

    if form.validate_on_submit():
        # Actualizar solo los campos relevantes para el cierre
        non_conformity.status = 'closed' # Cambiar estado a cerrado
        non_conformity.completion_date = datetime.utcnow() # Registrar fecha de cierre

        # Los campos verified_by_id y verification_date vienen en el modal de cierre
        non_conformity.verified_by_id = form.verified_by_id.data.id if form.verified_by_id.data else None
        non_conformity.verification_date = form.verification_date.data
        non_conformity.notes = form.notes.data # O un campo de notas específico para el cierre si es necesario

        non_conformity.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

        db.session.commit()
        flash('No Conformidad cerrada exitosamente!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la página de detalle correcta (Inspección o Auditoría)
    if non_conformity.inspection_id:
        return redirect(url_for('qm.inspection_detail', id=non_conformity.inspection_id))
    elif non_conformity.audit_id:
        # TODO: Redirigir a la página de detalle de auditoría cuando esté implementada
        flash('Redirección a auditoría no implementada', 'info')
        return redirect(url_for('qm.list_inspections')) # Redirigir a lista de inspecciones temporalmente
    else:
        # Esto no debería ocurrir si la comprobación inicial pasa
        return redirect(url_for('qm.list_inspections'))

@qm.route('/inspections/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_inspection(id):
    inspection = Inspection.query.get_or_404(id)
    
    # TODO: Agregar lógica de validación si es necesario (ej. solo cancelar si no está ya cerrada o cancelada)

    inspection.status = 'cancelled'
    inspection.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

    db.session.commit()
    flash('Inspección cancelada exitosamente!', 'success')
    return redirect(url_for('qm.inspection_detail', id=inspection.id))

@qm.route('/inspections/<int:id>/complete', methods=['POST'])
@login_required
def complete_inspection(id):
    inspection = Inspection.query.get_or_404(id)
    
    # TODO: Agregar lógica de validación si es necesario (ej. solo completar si no está ya completada o cancelada)
    # TODO: Considerar si se deben cerrar todas las no conformidades asociadas antes de completar

    inspection.status = 'completed'
    inspection.completion_date = datetime.utcnow() # Registrar fecha de finalización
    inspection.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

    db.session.commit()
    flash('Inspección marcada como completada!', 'success')
    return redirect(url_for('qm.inspection_detail', id=inspection.id))

# --- Rutas para Gestión de Certificados ---

@qm.route('/certificates')
@login_required
def list_certificates():
    # Implementar filtros de búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Definir cuántos elementos por página

    # Obtener parámetros de filtro
    search = request.args.get('search')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status') # Asumiendo que Certificate tiene campo status

    query = Certificate.query

    if search:
         query = query.filter(Certificate.certificate_number.ilike(f'%{search}%'))

    if type_filter and type_filter != '':
        query = query.filter_by(certificate_type=type_filter)

    if status_filter and status_filter != '':
         # Filtrar por estado si el modelo Certificate tiene ese campo
         # query = query.filter_by(status=status_filter)
         pass # TODO: Implementar filtro por estado si se añade campo status al modelo Certificate

    certificates = query.order_by(Certificate.issue_date.desc()).paginate(page=page, per_page=per_page)

    return render_template('qm/certificates.html', title='Gestión de Certificados', 
                           certificates=certificates, search=search, type=type_filter, status=status_filter)

@qm.route('/certificates/new', methods=['GET', 'POST'])
@login_required
def new_certificate():
    form = CertificateForm()
    if form.validate_on_submit():
        # TODO: Manejar subida de archivo
        # Lógica para manejar la subida de archivo
        file = form.certificate_file.data
        file_path = None # Inicializar la ruta del archivo como None
        if file:
            filename = secure_filename(file.filename)
            # Construir la ruta completa para guardar el archivo
            upload_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER_CERTIFICATES)
            file_full_path = os.path.join(upload_folder, filename)
            
            # Guardar el archivo
            try:
                file.save(file_full_path)
                # Guardar la ruta relativa en la base de datos
                file_path = os.path.join(UPLOAD_FOLDER_CERTIFICATES, filename)
            except Exception as e:
                flash(f'Error al guardar el archivo: {e}', 'danger')
                # Si falla la subida, podrías querer redirigir de nuevo o manejar el error de otra forma
                return render_template('qm/new_certificate.html', title='Nuevo Certificado', form=form)


        certificate = Certificate(
            certificate_number=form.certificate_number.data,
            certificate_type=form.certificate_type.data,
            reference_type=form.reference_type.data if form.reference_type.data != '' else None,
            reference_id=form.reference_id.data if form.reference_id.data != '' else None,
            issue_date=form.issue_date.data,
            expiry_date=form.expiry_date.data,
            issued_by=form.issued_by.data,
            file_path=file_path, # Guardar la ruta del archivo
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(certificate)
        db.session.commit()
        flash('Certificado creado exitosamente!', 'success')
        return redirect(url_for('qm.list_certificates'))
    return render_template('qm/new_certificate.html', title='Nuevo Certificado', form=form)

@qm.route('/certificates/<int:id>')
@login_required
def certificate_detail(id):
    certificate = Certificate.query.get_or_404(id)
    return render_template('qm/certificate_detail.html', title=f'Certificado #{certificate.certificate_number}', certificate=certificate)

@qm.route('/certificates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_certificate(id):
    certificate = Certificate.query.get_or_404(id)
    form = CertificateForm(obj=certificate)
    if form.validate_on_submit():
        # TODO: Manejar actualización del archivo si aplica
        # Lógica para manejar la actualización del archivo
        file = form.certificate_file.data
        if file:
            # Si se sube un nuevo archivo
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER_CERTIFICATES)
            file_full_path = os.path.join(upload_folder, filename)
            
            # Opcional: Eliminar archivo antiguo si existe
            if certificate.file_path and os.path.exists(os.path.join(current_app.root_path, certificate.file_path)):
                 try:
                     os.remove(os.path.join(current_app.root_path, certificate.file_path))
                 except Exception as e:
                     # Manejar error al eliminar archivo antiguo
                     flash(f'Advertencia: No se pudo eliminar el archivo antiguo: {e}', 'warning')

            # Guardar el nuevo archivo
            try:
                file.save(file_full_path)
                # Actualizar la ruta relativa en la base de datos
                certificate.file_path = os.path.join(UPLOAD_FOLDER_CERTIFICATES, filename)
            except Exception as e:
                flash(f'Error al guardar el nuevo archivo: {e}', 'danger')
                # Si falla la subida, podrías querer redirigir de nuevo o manejar el error
                return render_template('qm/new_certificate.html', title=f'Editar Certificado #{certificate.certificate_number}', form=form, certificate=certificate)
        # Si no se sube un nuevo archivo, certificate.file_path mantiene su valor existente (cargado por obj=certificate)

        # Actualizar los campos del objeto certificate con los datos del formulario (excluyendo el campo de archivo que ya manejamos)
        form.populate_obj(certificate, exclude=['certificate_file'])

        # Actualizar fecha de actualización
        certificate.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Certificado actualizado exitosamente!', 'success')
        return redirect(url_for('qm.certificate_detail', id=certificate.id))
    # Si es GET o el formulario no es válido, renderizar la plantilla con el formulario (pre-llenado en GET)
    # NOTA: En el caso de GET, el FileField no se pre-pobla por seguridad. El usuario tendrá que subir el archivo de nuevo si quiere cambiarlo.
    return render_template('qm/new_certificate.html', title=f'Editar Certificado #{certificate.certificate_number}', form=form, certificate=certificate)

@qm.route('/certificates/<int:id>/delete', methods=['POST'])
@login_required
def delete_certificate(id):
    certificate = Certificate.query.get_or_404(id)
    
    # Eliminar el archivo asociado si existe
    if certificate.file_path and os.path.exists(os.path.join(current_app.root_path, certificate.file_path)):
        try:
            os.remove(os.path.join(current_app.root_path, certificate.file_path))
            flash('Archivo de certificado eliminado correctamente.', 'info')
        except Exception as e:
            # Manejar error al eliminar archivo
            flash(f'Advertencia: No se pudo eliminar el archivo asociado: {e}', 'warning')
            
    # Eliminar el registro del certificado de la base de datos
    db.session.delete(certificate)
    db.session.commit()
    flash('Certificado eliminado exitosamente!', 'success')
    
    # Redirigir a la lista de certificados
    return redirect(url_for('qm.list_certificates'))

@qm.route('/certificates/<int:id>/download')
@login_required
def download_certificate(id):
    certificate = Certificate.query.get_or_404(id)
    
    if certificate.file_path and os.path.exists(os.path.join(current_app.root_path, certificate.file_path)):
        directory = os.path.join(current_app.root_path, UPLOAD_FOLDER_CERTIFICATES)
        # Extraer solo el nombre del archivo de la ruta completa guardada
        filename = os.path.basename(certificate.file_path)
        try:
            return send_from_directory(directory=directory, path=filename, as_attachment=True)
        except FileNotFoundError:
             flash('El archivo del certificado no fue encontrado.', 'danger')
    else:
        flash('No hay archivo asociado a este certificado.', 'warning')
        
    # Redirigir de vuelta a la página de detalle del certificado
    return redirect(url_for('qm.certificate_detail', id=certificate.id))

# --- Rutas para Gestión de Documentos ---

@qm.route('/documents')
@login_required
def list_documents():
    # Implementar filtros de búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Definir cuántos elementos por página

    # Obtener parámetros de filtro
    search = request.args.get('search')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')

    query = Document.query

    if search:
         query = query.filter(
             (Document.document_code.ilike(f'%{search}%')) |
             (Document.title.ilike(f'%{search}%'))
        )

    if type_filter and type_filter != '':
        query = query.filter_by(document_type=type_filter)

    if status_filter and status_filter != '':
        query = query.filter_by(status=status_filter)

    documents = query.order_by(Document.issue_date.desc()).paginate(page=page, per_page=per_page)

    return render_template('qm/documents.html', title='Gestión de Documentos', 
                           documents=documents, search=search, type=type_filter, status=status_filter)

@qm.route('/documents/new', methods=['GET', 'POST'])
@login_required
def new_document():
    form = DocumentForm()
    if form.validate_on_submit():
        # TODO: Manejar subida de archivo
        # Lógica para manejar la subida de archivo
        file = form.document_file.data
        file_path = None # Inicializar la ruta del archivo como None
        if file:
            filename = secure_filename(file.filename)
            # Construir la ruta completa para guardar el archivo
            upload_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER_DOCUMENTS)
            file_full_path = os.path.join(upload_folder, filename)
            
            # Guardar el archivo
            try:
                file.save(file_full_path)
                # Guardar la ruta relativa en la base de datos
                file_path = os.path.join(UPLOAD_FOLDER_DOCUMENTS, filename)
            except Exception as e:
                flash(f'Error al guardar el archivo: {e}', 'danger')
                # Si falla la subida, podrías querer redirigir de nuevo o manejar el error de otra forma
                return render_template('qm/new_document.html', title='Nuevo Documento', form=form)

        document = Document(
            document_code=form.document_code.data,
            title=form.title.data,
            version=form.version.data,
            document_type=form.document_type.data,
            issue_date=form.issue_date.data,
            revision_date=form.revision_date.data,
            status=form.status.data,
            file_path=file_path, # Guardar la ruta del archivo
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(document)
        db.session.commit()
        flash('Documento creado exitosamente!', 'success')
        return redirect(url_for('qm.list_documents'))
    return render_template('qm/new_document.html', title='Nuevo Documento', form=form)

@qm.route('/documents/<int:id>')
@login_required
def document_detail(id):
    document = Document.query.get_or_404(id)
    return render_template('qm/document_detail.html', title=f'Documento #{document.document_code}', document=document)

@qm.route('/documents/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(id):
    document = Document.query.get_or_404(id)
    form = DocumentForm(obj=document)
    if form.validate_on_submit():
        # TODO: Manejar actualización del archivo si aplica
        # Lógica para manejar la actualización del archivo
        file = form.document_file.data
        if file:
            # Si se sube un nuevo archivo
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER_DOCUMENTS)
            file_full_path = os.path.join(upload_folder, filename)
            
            # Opcional: Eliminar archivo antiguo si existe
            if document.file_path and os.path.exists(os.path.join(current_app.root_path, document.file_path)):
                 try:
                     os.remove(os.path.join(current_app.root_path, document.file_path))
                 except Exception as e:
                     # Manejar error al eliminar archivo antiguo
                     flash(f'Advertencia: No se pudo eliminar el archivo antiguo: {e}', 'warning')

            # Guardar el nuevo archivo
            try:
                file.save(file_full_path)
                # Actualizar la ruta relativa en la base de datos
                document.file_path = os.path.join(UPLOAD_FOLDER_DOCUMENTS, filename)
            except Exception as e:
                flash(f'Error al guardar el nuevo archivo: {e}', 'danger')
                # Si falla la subida, podrías querer redirigir de nuevo o manejar el error
                return render_template('qm/new_document.html', title=f'Editar Documento #{document.document_code}', form=form, document=document)
        # Si no se sube un nuevo archivo, document.file_path mantiene su valor existente (cargado por obj=document)

        # Actualizar los campos del objeto document con los datos del formulario (excluyendo el campo de archivo que ya manejamos)
        form.populate_obj(document, exclude=['document_file'])
        
        # Actualizar fecha de actualización
        document.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Documento actualizado exitosamente!', 'success')
        return redirect(url_for('qm.document_detail', id=document.id))
    # Si es GET o el formulario no es válido, renderizar la plantilla con el formulario (pre-llenado en GET)
    # NOTA: En el caso de GET, el FileField no se pre-pobla por seguridad. El usuario tendrá que subir el archivo de nuevo si quiere cambiarlo.
    return render_template('qm/new_document.html', title=f'Editar Documento #{document.document_code}', form=form, document=document)

@qm.route('/documents/<int:id>/obsolete', methods=['POST'])
@login_required
def make_document_obsolete(id):
    document = Document.query.get_or_404(id)
    
    # TODO: Agregar lógica de validación si es necesario (ej. solo marcar como obsoleto si no está ya en ese estado)

    document.status = 'obsolete' # Usar el estado 'obsoleto'
    document.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

    db.session.commit()
    flash(f'Documento #{document.document_code} marcado como obsoleto.', 'success')
    return redirect(url_for('qm.document_detail', id=document.id))

@qm.route('/documents/<int:id>/delete', methods=['POST'])
@login_required
def delete_document(id):
    document = Document.query.get_or_404(id)
    
    # Eliminar el archivo asociado si existe
    if document.file_path and os.path.exists(os.path.join(current_app.root_path, document.file_path)):
        try:
            os.remove(os.path.join(current_app.root_path, document.file_path))
            flash('Archivo de documento eliminado correctamente.', 'info')
        except Exception as e:
            # Manejar error al eliminar archivo
            flash(f'Advertencia: No se pudo eliminar el archivo asociado: {e}', 'warning')
            
    # Eliminar el registro del documento de la base de datos
    db.session.delete(document)
    db.session.commit()
    flash('Documento eliminado exitosamente!', 'success')
    
    # Redirigir a la lista de documentos
    return redirect(url_for('qm.list_documents'))

# --- Rutas para Gestión de Auditorías ---

@qm.route('/audits')
@login_required
def list_audits():
    # Implementar filtros de búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Definir cuántos elementos por página

    # Obtener parámetros de filtro
    search = request.args.get('search')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')

    query = Audit.query

    if search:
         query = query.filter(
             (Audit.audit_number.ilike(f'%{search}%')) |
             (Audit.scope.ilike(f'%{search}%')) |
             (Audit.audited_area.ilike(f'%{search}%'))
        )

    if type_filter and type_filter != '':
        query = query.filter_by(audit_type=type_filter)

    if status_filter and status_filter != '':
        query = query.filter_by(status=status_filter)

    audits = query.order_by(Audit.planned_date.desc()).paginate(page=page, per_page=per_page)

    return render_template('qm/audits.html', title='Gestión de Auditorías', 
                           audits=audits, search=search, type=type_filter, status=status_filter)

@qm.route('/audits/new', methods=['GET', 'POST'])
@login_required
def new_audit():
    form = AuditForm()
    if form.validate_on_submit():
        # --- Lógica para generar el número de auditoría automáticamente ---
        current_year = datetime.utcnow().year
        prefix = "AUD"
        # Buscar la última auditoría del año actual para obtener el último número
        last_audit = Audit.query.filter(
            Audit.audit_number.like(f'{prefix}-{str(current_year)[2:]}-%')
        ).order_by(desc(Audit.audit_number)).first()

        sequence_number = 1
        if last_audit and last_audit.audit_number:
            try:
                last_number_str = last_audit.audit_number.split('-')[-1]
                sequence_number = int(last_number_str) + 1
            except (ValueError, IndexError):
                sequence_number = 1 # Considerar loguear este error

        new_audit_number = f'{prefix}-{str(current_year)[2:]}-{sequence_number:04d}'
        # --- Fin de la lógica de generación de número ---

        audit = Audit(
            audit_number=new_audit_number, # Usar el número generado
            audit_type=form.audit_type.data,
            scope=form.scope.data,
            planned_date=form.planned_date.data,
            lead_auditor_id=form.lead_auditor_id.data.id if form.lead_auditor_id.data else None,
            audited_area=form.audited_area.data,
            status=form.status.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(audit)
        db.session.commit()
        flash('Auditoría creada exitosamente!', 'success')
        return redirect(url_for('qm.list_audits'))
    return render_template('qm/new_audit.html', title='Nueva Auditoría', form=form)

@qm.route('/audits/<int:id>')
@login_required
def audit_detail(id):
    audit = Audit.query.get_or_404(id)
    # Pasar formularios para modales de añadir/editar hallazgos
    form_new_finding = AuditFindingForm()
    form_edit_finding = AuditFindingForm() # Usar uno solo y llenarlo con JS
    
    return render_template('qm/audit_detail.html', title=f'Auditoría #{audit.audit_number}', 
                           audit=audit, form_new_finding=form_new_finding,
                           form_edit_finding=form_edit_finding)

@qm.route('/audits/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_audit(id):
    audit = Audit.query.get_or_404(id)
    form = AuditForm(obj=audit) # Pre-pobla el formulario con los datos existentes
    if form.validate_on_submit():
        # Actualizar los campos del objeto audit con los datos del formulario
        form.populate_obj(audit)
        # Manejar el campo lead_auditor_id por separado ya que es un QuerySelectField
        audit.lead_auditor_id = form.lead_auditor_id.data.id if form.lead_auditor_id.data else None

        # Actualizar fecha de actualización
        audit.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Auditoría actualizada exitosamente!', 'success')
        return redirect(url_for('qm.audit_detail', id=audit.id))
    # Si es GET o el formulario no es válido, renderizar la plantilla con el formulario (pre-llenado en GET)
    return render_template('qm/new_audit.html', title=f'Editar Auditoría #{audit.audit_number}', form=form, audit=audit)

@qm.route('/audits/<int:audit_id>/findings/add', methods=['POST'])
@login_required
def add_audit_finding(audit_id):
    audit = Audit.query.get_or_404(audit_id)
    form = AuditFindingForm()
    if form.validate_on_submit():
        finding = AuditFinding(
            audit_id=audit.id,
            finding_type=form.finding_type.data,
            description=form.description.data,
            severity=form.severity.data,
            status=form.status.data,
            assigned_to_id=form.assigned_to_id.data.id if form.assigned_to_id.data else None,
            due_date=form.due_date.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(finding)
        db.session.commit()
        flash('Hallazgo de Auditoría añadido exitosamente!', 'success')
    else:
         for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')
                
    return redirect(url_for('qm.audit_detail', id=audit.id))

@qm.route('/findings/<int:id>/edit', methods=['POST'])
@login_required
def edit_audit_finding(id):
    finding = AuditFinding.query.get_or_404(id)
    # Nos aseguramos de que el hallazgo pertenece a una auditoría
    if not finding.audit_id:
         abort(404)

    form = AuditFindingForm(obj=finding)
    if form.validate_on_submit():
        form.populate_obj(finding)
        # Manejar el campo assigned_to_id por separado
        finding.assigned_to_id = form.assigned_to_id.data.id if form.assigned_to_id.data else None

        finding.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Hallazgo de Auditoría actualizado exitosamente!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la página de detalle de la auditoría
    return redirect(url_for('qm.audit_detail', id=finding.audit_id))

@qm.route('/findings/<int:id>/close', methods=['POST'])
@login_required
def close_audit_finding(id):
    finding = AuditFinding.query.get_or_404(id)

    # Nos aseguramos de que el hallazgo pertenece a una auditoría
    if not finding.audit_id:
         abort(404)

    form = AuditFindingForm(obj=finding) # Usamos el mismo formulario base
    # Validar solo los campos necesarios para el cierre si es diferente del formulario de edición completo
    # Por ahora, validaremos el formulario completo como está definido.

    if form.validate_on_submit():
        # Actualizar solo los campos relevantes para el cierre
        finding.status = 'closed' # Cambiar estado a cerrado
        finding.completion_date = datetime.utcnow() # Registrar fecha de cierre

        # Los campos verified_by_id y verification_date vienen en el modal de cierre
        finding.verified_by_id = form.verified_by_id.data.id if form.verified_by_id.data else None
        finding.verification_date = form.verification_date.data
        finding.notes = form.notes.data # O un campo de notas específico para el cierre si es necesario

        finding.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

        db.session.commit()
        flash('Hallazgo de Auditoría cerrado exitosamente!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la página de detalle de la auditoría
    return redirect(url_for('qm.audit_detail', id=finding.audit_id))

@qm.route('/audits/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_audit(id):
    audit = Audit.query.get_or_404(id)
    
    # TODO: Agregar lógica de validación si es necesario (ej. solo cancelar si no está ya cerrada o cancelada)

    audit.status = 'cancelled'
    audit.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

    db.session.commit()
    flash('Auditoría cancelada exitosamente!', 'success')
    return redirect(url_for('qm.audit_detail', id=audit.id))

@qm.route('/audits/<int:id>/complete', methods=['POST'])
@login_required
def complete_audit(id):
    audit = Audit.query.get_or_404(id)
    
    # TODO: Agregar lógica de validación si es necesario (ej. solo completar si no está ya completada o cancelada)
    # TODO: Considerar si se deben cerrar todos los hallazgos asociados antes de completar

    audit.status = 'completed'
    audit.completion_date = datetime.utcnow() # Registrar fecha de finalización
    audit.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

    db.session.commit()
    flash('Auditoría marcada como completada!', 'success')
    return redirect(url_for('qm.audit_detail', id=audit.id))

@qm.route('/documents/<int:id>/download')
@login_required
def download_document(id):
    document = Document.query.get_or_404(id)
    
    if document.file_path and os.path.exists(os.path.join(current_app.root_path, document.file_path)):
        directory = os.path.join(current_app.root_path, UPLOAD_FOLDER_DOCUMENTS)
        # Extraer solo el nombre del archivo de la ruta completa guardada
        filename = os.path.basename(document.file_path)
        try:
            return send_from_directory(directory=directory, path=filename, as_attachment=True)
        except FileNotFoundError:
             flash('El archivo del documento no fue encontrado.', 'danger')
    else:
        flash('No hay archivo asociado a este documento.', 'warning')
        
    # Redirigir de vuelta a la página de detalle del documento
    return redirect(url_for('qm.document_detail', id=document.id))

@qm.route('/audits/<int:audit_id>/finding/<int:finding_id>/delete', methods=['POST'])
@login_required
def delete_audit_finding(audit_id, finding_id):
    # TODO: Implementar lógica para eliminar un hallazgo de auditoría
    finding = AuditFinding.query.get_or_404(finding_id)
    audit_id = finding.audit_id # Asegurarse de tener el audit_id antes de eliminar
    db.session.delete(finding)
    db.session.commit()
    flash('Hallazgo de auditoría eliminado correctamente.', 'success')
    return redirect(url_for('qm.audit_detail', audit_id=audit_id))

# TODO: Add routes for Certificate and Document nested items (e.g., related files)
# TODO: Add routes for CAPAs related to QM items
# TODO: Implement quality checks and non-conformity workflows fully
# TODO: Implement file upload/download for Documents and Certificates
# TODO: Add filtering, sorting, and pagination to list views
# TODO: Implement search functionality
# TODO: Add user roles and permissions checks
# TODO: Implement reporting and analytics for QM data

@qm.route('/certificates/<int:certificate_id>/upload_file', methods=['POST'])
@login_required
def upload_certificate_file(certificate_id):
    # TODO: Implement file upload logic for certificates
    pass # Placeholder

@qm.route('/documents/<int:document_id>/upload_file', methods=['POST'])
@login_required
def upload_document_file(document_id):
    # TODO: Implement file upload logic for documents
    pass # Placeholder

@qm.route('/certificates/<int:certificate_id>/download_file')
@login_required
def download_certificate_file(certificate_id):
    # TODO: Implement file download logic for certificates
    pass # Placeholder

@qm.route('/documents/<int:document_id>/download_file')
@login_required
def download_document_file(document_id):
    # TODO: Implement file download logic for documents
    pass # Placeholder

# --- Rutas para Gestión de CAPAs ---

@qm.route('/capas')
@login_required
def list_capas():
    # Implementar filtros de búsqueda y paginación para CAPAs
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Definir cuántos elementos por página

    # Obtener parámetros de filtro de la URL (TODO: implementar filtros)
    search = request.args.get('search')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')

    query = CAPA.query

    # TODO: Añadir lógica de filtrado
    # if search:
    #     query = query.filter(...)
    # if type_filter:
    #     query = query.filter_by(capa_type=type_filter)
    # if status_filter:
    #     query = query.filter_by(status=status_filter)

    capas = query.order_by(CAPA.created_at.desc()).paginate(page=page, per_page=per_page)

    return render_template('qm/capas.html', title='Gestión de CAPAs', 
                           capas=capas, search=search, type=type_filter, status=status_filter)

@qm.route('/capas/new', methods=['GET', 'POST'])
@login_required
def new_capa():
    form = CAPAForm()
    if form.validate_on_submit():
        # --- Lógica para generar el número de CAPA automáticamente ---
        current_year = datetime.utcnow().year
        prefix = "CAPA"
        # Buscar la última CAPA del año actual para obtener el último número
        last_capa = CAPA.query.filter(
            CAPA.capa_number.like(f'{prefix}-{str(current_year)[2:]}-%')
        ).order_by(desc(CAPA.capa_number)).first()

        sequence_number = 1
        if last_capa and last_capa.capa_number:
            try:
                last_number_str = last_capa.capa_number.split('-')[-1]
                sequence_number = int(last_number_str) + 1
            except (ValueError, IndexError):
                sequence_number = 1 # Considerar loguear este error

        new_capa_number = f'{prefix}-{str(current_year)[2:]}-{sequence_number:04d}'
        # --- Fin de la lógica de generación de número ---

        capa = CAPA(
            capa_number=new_capa_number, # Usar el número generado
            capa_type=form.capa_type.data,
            source_type=form.source_type.data if form.source_type.data != '' else None,
            source_id=form.source_id.data if form.source_id.data is not None else None,
            description=form.description.data,
            root_cause=form.root_cause.data,
            proposed_action=form.proposed_action.data,
            implemented_action=form.implemented_action.data,
            status=form.status.data,
            assigned_to_id=form.assigned_to_id.data.id if form.assigned_to_id.data else None,
            due_date=form.due_date.data,
            completion_date=form.completion_date.data,
            verification_method=form.verification_method.data,
            verified_by_id=form.verified_by_id.data.id if form.verified_by_id.data else None,
            verification_date=form.verification_date.data,
            effectiveness_status=form.effectiveness_status.data if form.effectiveness_status.data != '' else None,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(capa)
        db.session.commit()
        flash('CAPA creada exitosamente!', 'success')
        return redirect(url_for('qm.list_capas'))
    # Si es GET o el formulario no es válido, renderizar la plantilla
    return render_template('qm/new_capa.html', title='Nueva CAPA', form=form)

@qm.route('/capas/<int:id>')
@login_required
def capa_detail(id):
    # TODO: Implementar vista de detalle para CAPA
    capa = CAPA.query.get_or_404(id)
    # Pasar formulario para modal de cierre si es necesario
    form_close_capa = CAPAForm() # Usar uno solo y llenarlo con JS para cerrar
    return render_template('qm/capa_detail.html', title=f'CAPA #{capa.capa_number}', capa=capa, form_close_capa=form_close_capa)

@qm.route('/capas/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_capa(id):
    # TODO: Implementar lógica de edición para CAPA
    capa = CAPA.query.get_or_404(id)
    form = CAPAForm(obj=capa) # Pre-pobla el formulario
    if form.validate_on_submit():
        # Actualizar campos
        form.populate_obj(capa)
        # Manejar campos QuerySelectField si es necesario (assigned_to_id, verified_by_id)
        capa.assigned_to_id = form.assigned_to_id.data.id if form.assigned_to_id.data else None
        capa.verified_by_id = form.verified_by_id.data.id if form.verified_by_id.data else None

        capa.updated_at = datetime.utcnow()
        db.session.commit()
        flash('CAPA actualizada exitosamente!', 'success')
        return redirect(url_for('qm.capa_detail', id=capa.id))
    # Si es GET o formulario inválido
    return render_template('qm/new_capa.html', title=f'Editar CAPA #{capa.capa_number}', form=form, capa=capa)

@qm.route('/capas/<int:id>/close', methods=['POST'])
@login_required
def close_capa(id):
    # TODO: Implementar lógica de cierre para CAPA
    capa = CAPA.query.get_or_404(id)
    form = CAPAForm(obj=capa) # Usamos el mismo formulario base

    if form.validate_on_submit():
        # Actualizar solo los campos relevantes para el cierre
        capa.status = 'closed' # Cambiar estado a cerrado
        capa.completion_date = datetime.utcnow() # Registrar fecha de cierre

        # Campos verified_by_id y verification_date del modal de cierre
        capa.verified_by_id = form.verified_by_id.data.id if form.verified_by_id.data else None
        capa.verification_date = form.verification_date.data
        capa.notes = form.notes.data # O un campo de notas específico para el cierre si es necesario

        capa.updated_at = datetime.utcnow() # Actualizar timestamp de modificación

        db.session.commit()
        flash('CAPA cerrada exitosamente!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la página de detalle de la CAPA
    return redirect(url_for('qm.capa_detail', id=capa.id))