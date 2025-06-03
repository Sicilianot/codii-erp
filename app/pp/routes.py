from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.pp import Product, ProductCategory, ProductMaterial, ProductionOrder, ProductionOperation, ProductionMaterial, QualityCheck
from app.models.mm import Material
from app.forms.pp import ProductForm, ProductCategoryForm, ProductMaterialForm, ProductionOrderForm, ProductionOperationForm, QualityCheckForm
from datetime import datetime, time
import uuid
from app.models.user import User

bp = Blueprint('pp', __name__)

# Rutas para Categorías de Producto
@bp.route('/categories')
@login_required
def list_categories():
    search = request.args.get('search')
    status = request.args.get('status', 'all')

    query = ProductCategory.query

    if search:
        query = query.filter(ProductCategory.name.ilike(f'%{search}%'))

    if status != 'all':
        query = query.filter(ProductCategory.is_active == (status == 'active'))

    categories = query.all()

    return render_template('pp/categories.html', categories=categories, search=search, status=status)

@bp.route('/categories/new', methods=['POST'])
@login_required
def new_category():
    form = ProductCategoryForm()
    if form.validate_on_submit():
        category = ProductCategory(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            is_active=form.is_active.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Categoría creada exitosamente.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la lista de categorías con los filtros actuales
    return redirect(url_for('pp.list_categories', search=request.form.get('search_redirect'), status=request.form.get('status_redirect')))

@bp.route('/categories/<int:id>/edit', methods=['POST'])
@login_required
def edit_category(id):
    category = ProductCategory.query.get_or_404(id)
    form = ProductCategoryForm()
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.color = form.color.data
        category.is_active = form.is_active.data
        db.session.commit()
        flash('Categoría actualizada exitosamente.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir de vuelta a la lista de categorías con los filtros actuales
    return redirect(url_for('pp.list_categories', search=request.form.get('search_redirect'), status=request.form.get('status_redirect')))

@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = ProductCategory.query.get_or_404(id)
    if category.products:
        flash('No se puede eliminar la categoría porque tiene productos asociados.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Categoría eliminada exitosamente.', 'success')
    
    # Redirigir de vuelta a la lista de categorías con los filtros actuales
    return redirect(url_for('pp.list_categories', search=request.form.get('search_redirect'), status=request.form.get('status_redirect')))

# Rutas para Productos
@bp.route('/products')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', 'all')

    query = Product.query.join(ProductCategory)

    if search:
        query = query.filter( (Product.code.ilike(f'%{search}%')) | (Product.name.ilike(f'%{search}%')) )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if status != 'all':
        query = query.filter(Product.is_active == (status == 'active'))

    products = query.paginate(page=page, per_page=10) # Ajustar per_page según sea necesario
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    materials = Material.query.order_by(Material.name).all() # Para el modal de materiales en productos.html

    return render_template('pp/products.html', products=products, categories=categories, materials=materials, search=search, category_id=category_id, status=status)

@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    materials = Material.query.order_by(Material.name).all()

    if form.validate_on_submit():
        product = Product(
            code=form.code.data,
            name=form.name.data,
            description=form.description.data,
            category_id=form.category_id.data,
            unit=form.unit.data,
            standard_time=form.standard_time.data,
            is_active=form.is_active.data
        )
        db.session.add(product)
        db.session.flush() # Obtener el ID del producto antes de guardar materiales

        # Procesar materiales del formulario
        material_ids = request.form.getlist('materials[]')
        quantities = request.form.getlist('quantities[]')
        notes = request.form.getlist('notes[]')

        for i in range(len(material_ids)):
            if material_ids[i] and quantities[i]:
                product_material = ProductMaterial(
                    product_id=product.id,
                    material_id=int(material_ids[i]),
                    quantity_required=float(quantities[i]), # Cambiado de quantity a quantity_required
                    notes=notes[i] if notes[i] else None
                )
                db.session.add(product_material)

        db.session.commit()
        flash('Producto creado exitosamente.', 'success')
        return redirect(url_for('pp.list_products'))

    return render_template('pp/product_form.html', form=form, categories=categories, materials=materials, product=None)

@bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    materials = Material.query.order_by(Material.name).all()

    if form.validate_on_submit():
        product.code = form.code.data
        product.name = form.name.data
        product.description = form.description.data
        product.category_id = form.category_id.data
        product.unit = form.unit.data
        product.standard_time = form.standard_time.data
        product.is_active = form.is_active.data

        # Eliminar materiales existentes y agregar los nuevos del formulario
        ProductMaterial.query.filter_by(product_id=product.id).delete()
        db.session.flush()

        material_ids = request.form.getlist('materials[]')
        quantities = request.form.getlist('quantities[]')
        notes = request.form.getlist('notes[]')

        for i in range(len(material_ids)):
             if material_ids[i] and quantities[i]:
                product_material = ProductMaterial(
                    product_id=product.id,
                    material_id=int(material_ids[i]),
                    quantity_required=float(quantities[i]),
                    notes=notes[i] if notes[i] else None
                )
                db.session.add(product_material)

        db.session.commit()
        flash('Producto actualizado exitosamente.', 'success')
        return redirect(url_for('pp.list_products'))

    # Si es GET, pasar los materiales existentes para mostrarlos en la tabla
    product_materials_data = []
    if request.method == 'GET' and product.materials:
         for pm in product.materials:
             product_materials_data.append({
                 'material_id': pm.material_id,
                 'material_name': pm.material.name,
                 'quantity': pm.quantity_required,
                 'unit': pm.material.unit,
                 'notes': pm.notes
             })

    return render_template('pp/product_form.html', form=form, categories=categories, materials=materials, product=product, product_materials_data=product_materials_data)

# API para obtener tiempo estándar de un producto
@bp.route('/api/product/<int:id>/standard-time')
@login_required
def api_product_standard_time(id):
    product = Product.query.get_or_404(id)
    return jsonify({'standard_time': product.standard_time})

# Rutas para Órdenes de Producción
@bp.route('/orders')
@login_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    status = request.args.get('status', 'all')
    priority = request.args.get('priority', 'all')

    query = ProductionOrder.query.join(Product)

    if search:
        query = query.filter( (ProductionOrder.order_number.ilike(f'%{search}%')) | (Product.name.ilike(f'%{search}%')) )

    if status != 'all':
        query = query.filter(ProductionOrder.status == status)

    if priority != 'all':
        query = query.filter(ProductionOrder.priority == priority)

    orders = query.order_by(ProductionOrder.planned_start.desc()).paginate(page=page, per_page=10)

    # Pasar fecha y hora actual y inicio del día para los KPIs de la plantilla
    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)

    return render_template('pp/orders.html', orders=orders, search=search, status=status, priority=priority, now=now, today_start=today_start)

@bp.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    form = ProductionOrderForm()
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()

    if form.validate_on_submit():
        # Generar número de orden único (ejemplo simple)
        order_number = f'OP-{uuid.uuid4().hex[:6].upper()}'

        order = ProductionOrder(
            order_number=order_number,
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            planned_start=form.planned_start.data,
            planned_end=form.planned_end.data,
            priority=form.priority.data,
            notes=form.notes.data,
            created_by=current_user
            # status se establece por defecto en 'pending' en el modelo
        )
        db.session.add(order)
        db.session.flush() # Obtener el ID de la orden antes de guardar relaciones
        product = Product.query.get(form.product_id.data) # Obtener el producto seleccionado

        # Generar operaciones basadas en el tiempo estándar del producto (ejemplo: una operación principal)
        if product.standard_time and order.quantity > 0:
            # TODO: Considerar un enfoque más robusto si hay múltiples operaciones definidas en el producto
            # Por ahora, creamos una operación genérica con duración calculada
            operation = ProductionOperation(
                production_order_id=order.id,
                operation_type='Producción Principal', # Tipo de operación genérico
                sequence=1, # Secuencia inicial
                planned_duration=product.standard_time * order.quantity, # Duración total estimada
                # status se establece por defecto en 'pending'
            )
            db.session.add(operation)

        # Generar materiales de orden basados en los materiales del producto
        if product.materials:
            for product_material in product.materials:
                order_material = ProductionMaterial(
                    production_order_id=order.id,
                    material_id=product_material.material_id,
                    quantity_required=product_material.quantity_required * order.quantity, # Cantidad total requerida
                    # quantity_used se establece por defecto en 0
                )
                db.session.add(order_material)

        db.session.commit()
        flash(f'Orden de Producción #{order.order_number} creada exitosamente.', 'success')
        return redirect(url_for('pp.list_orders'))

    # Si es GET, establecer fecha/hora actual como valor por defecto para planned_start en el formulario
    if request.method == 'GET':
         from datetime import datetime
         form.planned_start.data = datetime.now()

    return render_template('pp/order_form.html', form=form, products=products)

@bp.route('/orders/<int:id>')
@login_required
def order_detail(id):
    order = ProductionOrder.query.get_or_404(id)
    # Cargar relaciones para evitar N+1 queries si no están configuradas con lazy='joined'
    # order = ProductionOrder.query.options(db.joinedload(ProductionOrder.product), db.joinedload(ProductionOrder.operations), db.joinedload(ProductionOrder.materials), db.joinedload(ProductionOrder.quality_checks)).get_or_404(id)
    return render_template('pp/order_detail.html', order=order)

@bp.route('/orders/<int:id>/start', methods=['POST'])
@login_required
def start_order(id):
    order = ProductionOrder.query.get_or_404(id)
    if order.status == 'pending':
        order.status = 'in_progress'
        from datetime import datetime
        order.actual_start = datetime.now()
        db.session.commit()
        flash(f'Orden #{order.order_number} iniciada.', 'success')
    else:
        flash(f'La Orden #{order.order_number} no se puede iniciar en estado {order.status}.', 'warning')
    return redirect(url_for('pp.order_detail', id=order.id))

@bp.route('/orders/<int:id>/complete', methods=['POST'])
@login_required
def complete_order(id):
    order = ProductionOrder.query.get_or_404(id)

    if order.status == 'in_progress':
        # Lógica de Verificación Antes de Completar
        # Verificar si todas las operaciones están completadas
        all_operations_completed = all(op.status == 'completed' for op in order.operations)
        if not order.operations: # Si no hay operaciones definidas, asumimos que no son requeridas para completarla
            all_operations_completed = True

        # TODO: Verificar si los materiales requeridos han sido registrados como usados (puede ser un umbral o exacto)
        # Esta verificación puede ser compleja dependiendo de la tolerancia.
        # Por ahora, solo verificamos si se han agregado materiales de orden.
        materials_recorded = len(order.materials) > 0
        if not order.materials: # Si no hay materiales definidos para el producto, no son requeridos
            materials_recorded = True

        # Verificar si los controles de calidad requeridos han sido realizados y aprobados
        # TODO: Implementar lógica para definir qué controles de calidad son 'requeridos'
        # Por ahora, verificamos si hay *algún* control de calidad registrado y aprobado si existen controles.
        quality_checks_passed = True
        if order.quality_checks:
            quality_checks_passed = any(qc.status == 'approved' for qc in order.quality_checks) # Verifica si al menos uno fue aprobado
        # TODO: Considerar casos donde no se requieren controles o se requieren múltiples aprobaciones

        if all_operations_completed and materials_recorded and quality_checks_passed:
            # Fin Lógica de Verificación

            order.status = 'completed'
            from datetime import datetime
            order.actual_end = datetime.now()
            db.session.commit()
            flash(f'Orden #{order.order_number} completada exitosamente.', 'success')
        else:
            # Mensajes de advertencia si las verificaciones fallan
            if not all_operations_completed:
                flash('No se puede completar la orden: Hay operaciones pendientes o en progreso.', 'warning')
            if not materials_recorded:
                flash('Advertencia: No se han registrado materiales usados para esta orden.', 'warning')
            if order.quality_checks and not quality_checks_passed:
                flash('Advertencia: Ninguno de los controles de calidad registrados ha sido aprobado.', 'warning')
            # Si a pesar de las advertencias se quiere completar, se podría añadir una opción forzada o un permiso especial
            # Por ahora, bloqueamos la finalización si las operaciones no están completas.
            if all_operations_completed: # Solo permitimos avanzar si al menos las operaciones están completas
                order.status = 'completed' # Forzamos la finalización a pesar de advertencias de materiales/calidad
                from datetime import datetime
                order.actual_end = datetime.now()
                db.session.commit()
                flash(f'Orden #{order.order_number} completada con advertencias sobre materiales o calidad.', 'warning')

    else:
        flash(f'La Orden #{order.order_number} no se puede completar en estado {order.status}.', 'warning')

    return redirect(url_for('pp.order_detail', id=order.id))

# Rutas para Operaciones de Producción
@bp.route('/operations/<int:id>/start', methods=['POST'])
@login_required
def start_operation(id):
    operation = ProductionOperation.query.get_or_404(id)
    if operation.status == 'pending':
        operation.status = 'in_progress'
        from datetime import datetime
        operation.actual_start = datetime.now()
        operation.operator = current_user # Asignar el usuario actual como operador
        db.session.commit()
        flash(f'Operación {operation.sequence} ({operation.operation_type}) iniciada.', 'success')
    else:
        flash(f'La Operación {operation.sequence} no se puede iniciar en estado {operation.status}.', 'warning')
    
    # Redirigir al detalle de la orden asociada
    return redirect(url_for('pp.order_detail', id=operation.production_order_id))

@bp.route('/operations/<int:id>/complete', methods=['POST'])
@login_required
def complete_operation(id):
    operation = ProductionOperation.query.get_or_404(id)
    order = operation.production_order # Obtener la orden asociada

    if operation.status == 'in_progress':
        operation.status = 'completed'
        from datetime import datetime
        operation.actual_end = datetime.now()
        
        # Calcular duración real en minutos
        if operation.actual_start and operation.actual_end:
            duration = (operation.actual_end - operation.actual_start).total_seconds() / 60
            operation.actual_duration = round(duration, 2)

        db.session.commit()
        flash(f'Operación {operation.sequence} ({operation.operation_type}) completada.', 'success')

        # Lógica para Actualizar Progreso de la Orden
        # Calcular el porcentaje de operaciones completadas
        total_operations = len(order.operations)
        completed_operations = sum(1 for op in order.operations if op.status == 'completed')

        if total_operations > 0:
            order.progress = round((completed_operations / total_operations) * 100, 2)
        else:
            order.progress = 100 # Si no hay operaciones, se considera 100% completada la etapa de operaciones

        db.session.commit() # Guardar el progreso actualizado
        # Fin Lógica para Actualizar Progreso

    else:
        flash(f'La Operación {operation.sequence} no se puede completar en estado {operation.status}.', 'warning')
        
    # Redirigir al detalle de la orden asociada
    return redirect(url_for('pp.order_detail', id=operation.production_order_id))

@bp.route('/orders/<int:order_id>/add_operation', methods=['POST'])
@login_required
def add_operation(order_id):
    order = ProductionOrder.query.get_or_404(order_id)
    form = ProductionOperationForm()
    if form.validate_on_submit():
        operation = ProductionOperation(
            production_order_id=order.id,
            operation_type=form.operation_type.data,
            sequence=form.sequence.data,
            planned_duration=form.planned_duration.data,
            notes=form.notes.data
            # status se establece por defecto en 'pending'
        )
        db.session.add(operation)
        db.session.commit()
        flash('Operación agregada a la orden.', 'success')

        # TODO: Recalcular el progreso de la orden después de añadir una operación si es necesario

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')

    # Redirigir al detalle de la orden
    return redirect(url_for('pp.order_detail', id=order.id))

# Rutas para Controles de Calidad
@bp.route('/quality-checks/new/<int:order_id>', methods=['GET', 'POST'])
@login_required
def new_quality_check(order_id):
    order = ProductionOrder.query.get_or_404(order_id)
    form = QualityCheckForm()
    users = User.query.order_by(User.name).all() # O filtrar por rol si es necesario

    # Configurar choices del SelectField para inspector_id
    form.inspector_id.choices = [(u.id, u.name) for u in users]
    form.inspector_id.choices.insert(0, ('', 'Seleccione Inspector')) # Opción por defecto

    if form.validate_on_submit():
        # Convertir el valor del select en entero si no es None o vacío
        inspector_id = int(form.inspector_id.data) if form.inspector_id.data else None

        check = QualityCheck(
            production_order_id=order.id,
            check_type=form.check_type.data,
            status=form.status.data,
            result=form.result.data,
            check_date=form.check_date.data,
            inspector_id=inspector_id,
            notes=form.notes.data
        )
        db.session.add(check)
        db.session.commit()
        flash('Control de calidad registrado exitosamente.', 'success')
        return redirect(url_for('pp.order_detail', id=order.id))

    # Si es GET, establecer la fecha actual como valor por defecto
    if request.method == 'GET':
        from datetime import datetime
        form.check_date.data = datetime.now()

    return render_template('pp/quality_check_form.html', form=form, order=order)

# API para obtener materiales de un producto
@bp.route('/api/product/<int:id>/materials')
@login_required
def get_product_materials(id):
    product = Product.query.get_or_404(id)
    materials = [{
        'id': pm.material.id,
        'name': pm.material.name,
        'quantity': pm.quantity,
        'unit': pm.material.unit
    } for pm in product.materials]
    return jsonify(materials) 