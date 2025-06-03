from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models import Product, ProductComponent, ProductProcess, ProductionOrder, ProductionOrderItem, ProductionProcess, ProductCategory # Actualizada la importación de modelos
from app.forms.pp import ProductForm, ProductComponentForm, ProductProcessForm, ProductionOrderForm, ProductionOrderItemForm, ProductCategoryForm # Importar los formularios
from sqlalchemy.orm import joinedload
from datetime import datetime

pp = Blueprint('pp', __name__, url_prefix='/pp')

# --- Rutas para Productos ---

# Ruta para listar productos
@pp.route('/products')
@login_required
def list_products():
    # Obtener todos los productos de la base de datos
    products = Product.query.all()
    # TODO: Crear plantilla list_products.html
    return render_template('pp/list_products.html', products=products)

# Ruta para añadir un nuevo producto
@pp.route('/products/new', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm() # Crear instancia del formulario
    if form.validate_on_submit():
        # Crear y guardar nuevo producto
        new_product = Product(
            code=form.code.data,
            name=form.name.data,
            description=form.description.data,
            product_type=form.product_type.data,
            material_type=form.material_type.data,
            unit_of_measure=form.unit_of_measure.data,
            standard_price=form.standard_price.data,
            estimated_production_time=form.estimated_production_time.data,
            weight=form.weight.data,
            dimensions=form.dimensions.data,
            is_active=form.is_active.data
            # technical_specs y welding_specs son JSON, manejarlos si es necesario
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Producto creado exitosamente!', 'success')
        return redirect(url_for('pp.list_products'))
    # TODO: Crear plantilla add_edit_product.html
    return render_template('pp/add_edit_product.html', title='Añadir Nuevo Producto', form=form)

# Ruta para editar un producto existente
@pp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    # Obtener producto por ID o 404
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product) # Precargar formulario

    if form.validate_on_submit():
        # Actualizar datos del producto y guardar
        product.code = form.code.data
        product.name = form.name.data
        product.description = form.description.data
        product.product_type = form.product_type.data
        product.material_type = form.material_type.data
        product.unit_of_measure = form.unit_of_measure.data
        product.standard_price = form.standard_price.data
        product.estimated_production_time = form.estimated_production_time.data
        product.weight = form.weight.data
        product.dimensions = form.dimensions.data
        product.is_active = form.is_active.data
        # technical_specs y welding_specs son JSON, manejarlos si es necesario

        db.session.commit()
        flash('Producto actualizado exitosamente!', 'success')
        return redirect(url_for('pp.list_products'))

    # TODO: Crear plantilla add_edit_product.html
    return render_template('pp/add_edit_product.html', title='Editar Producto', form=form)

# Ruta para eliminar un producto (solo POST)
@pp.route('/products/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    # Obtener producto por ID o 404 y eliminar
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Producto eliminado exitosamente!', 'success')
    return redirect(url_for('pp.list_products'))

# Ruta para ver detalles de un producto
@pp.route('/products/<int:id>')
@login_required
def view_product(id):
    # Obtener producto por ID o 404, cargando relaciones con componentes y procesos
    product = Product.query.options(joinedload(Product.components), joinedload(Product.processes)).get_or_404(id)
    # TODO: Crear plantilla view_product.html
    return render_template('pp/view_product.html', product=product)

# TODO: Add routes for ProductComponent (BOM) and ProductProcess (Routing) management

# --- Rutas para Componentes de Producto (BOM) ---

# Ruta para añadir un nuevo componente a la BOM de un producto (POST desde modal/formulario)
@pp.route('/products/<int:product_id>/add_component', methods=['POST'])
@login_required
def add_product_component(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductComponentForm() # type: ignore # Crear instancia del formulario

    # Si usamos QuerySelectField en el formulario, validate_on_submit() se encargará de validar
    if form.validate_on_submit():
        # Crear y guardar nuevo componente
        new_component = ProductComponent(
            product=product, # Asignar el componente al producto
            material=form.material.data, # QuerySelectField devuelve el objeto Material
            quantity=form.quantity.data,
            unit_of_measure=form.unit_of_measure.data,
            weight=form.weight.data,
            position=form.position.data,
            notes=form.notes.data
        )
        db.session.add(new_component)
        db.session.commit()

        # TODO: Recalcular el peso total del producto si es necesario
        # Recalcular peso total del producto
        product.calculate_total_weight() # type: ignore
        db.session.commit()

        flash('Componente añadido a la BOM exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalles del producto
        return redirect(url_for('pp.view_product', id=product.id))
    else:
        # Si hay errores de validación, flashear los errores y redirigir
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalles del producto, posiblemente indicando qué modal reabrir
        return redirect(url_for('pp.view_product', id=product.id, modal='addComponentModal')) # Asumiendo un modal con este ID

# Ruta para editar un componente de la BOM (POST desde modal/formulario)
@pp.route('/product_components/edit/<int:component_id>', methods=['POST'])
@login_required
def edit_product_component(component_id):
    component = ProductComponent.query.get_or_404(component_id)
    product = component.product # Obtener el producto padre
    form = ProductComponentForm(obj=component) # type: ignore # Precargar formulario

    if form.validate_on_submit():
        # Actualizar datos del componente
        component.material = form.material.data
        component.quantity = form.quantity.data
        component.unit_of_measure = form.unit_of_measure.data
        component.weight = form.weight.data
        component.position = form.position.data
        component.notes = form.notes.data

        db.session.commit()

        # TODO: Recalcular el peso total del producto si es necesario
        # Recalcular peso total del producto
        product.calculate_total_weight() # type: ignore
        db.session.commit()

        flash('Componente de la BOM actualizado exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalles del producto
        return redirect(url_for('pp.view_product', id=product.id))
    else:
        # Si hay errores de validación, flashear los errores y redirigir
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalles del producto, indicando qué modal reabrir
        return redirect(url_for('pp.view_product', id=product.id, modal=f'editComponentModal{component_id}')) # Asumiendo modales con estos IDs

# Ruta para eliminar un componente de la BOM (solo POST)
@pp.route('/product_components/delete/<int:component_id>', methods=['POST'])
@login_required
def delete_product_component(component_id):
    component = ProductComponent.query.get_or_404(component_id)
    product = component.product # Obtener el producto padre
    db.session.delete(component)
    db.session.commit()

    # TODO: Recalcular el peso total del producto si es necesario
    # Recalcular peso total del producto
    product.calculate_total_weight() # type: ignore
    db.session.commit()

    flash('Componente de la BOM eliminado exitosamente!', 'success')
    # Redirigir de vuelta a la página de detalles del producto
    return redirect(url_for('pp.view_product', id=product.id))

# --- Rutas para Procesos de Producto (Routing) ---

# Ruta para añadir un nuevo proceso a la Hoja de Ruta de un producto (POST desde modal/formulario)
@pp.route('/products/<int:product_id>/add_process', methods=['POST'])
@login_required
def add_product_process(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductProcessForm() # type: ignore # Crear instancia del formulario

    if form.validate_on_submit():
        # Crear y guardar nuevo proceso
        new_process = ProductProcess(
            product=product, # Asignar el proceso al producto
            process_type=form.process_type.data,
            sequence=form.sequence.data,
            estimated_time=form.estimated_time.data,
            notes=form.notes.data,
            # TODO: Handle JSON fields: required_skills, parameters, quality_checks
            required_skills=form.required_skills.data or None, # Manejar campo JSON
            parameters=form.parameters.data or None, # Manejar campo JSON
            quality_checks=form.quality_checks.data or None # Manejar campo JSON
        )
        # Convertir strings JSON a objetos Python (dict/list) si es necesario antes de guardar, SQLAlchemy JSON type puede manejarlo
        # Aquí asumimos que SQLAlchemy convierte automáticamente la cadena JSON si el campo está definido como db.JSON
        # Validar si las cadenas son JSON válidas podría ser necesario para evitar errores de DB

        db.session.add(new_process)
        db.session.commit()

        flash('Proceso añadido a la Hoja de Ruta exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalles del producto
        return redirect(url_for('pp.view_product', id=product.id))
    else:
        # Si hay errores de validación, flashear los errores y redirigir
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalles del producto, posiblemente indicando qué modal reabrir
        return redirect(url_for('pp.view_product', id=product.id, modal='addProcessModal')) # Asumiendo un modal con este ID

# Ruta para editar un proceso de la Hoja de Ruta (POST desde modal/formulario)
@pp.route('/product_processes/edit/<int:process_id>', methods=['POST'])
@login_required
def edit_product_process(process_id):
    process = ProductProcess.query.get_or_404(process_id)
    product = process.product # Obtener el producto padre
    form = ProductProcessForm(obj=process) # type: ignore # Precargar formulario

    if form.validate_on_submit():
        # Actualizar datos del proceso
        process.process_type = form.process_type.data
        process.sequence = form.sequence.data
        process.estimated_time = form.estimated_time.data
        process.notes = form.notes.data
        # TODO: Handle JSON fields: required_skills, parameters, quality_checks
        process.required_skills = form.required_skills.data or None # Manejar campo JSON
        process.parameters = form.parameters.data or None # Manejar campo JSON
        process.quality_checks = form.quality_checks.data or None # Manejar campo JSON

        # Actualizar campos de operador y horas reales
        process.operator = form.operator.data # QuerySelectField devuelve el objeto User o None
        process.actual_hours = form.actual_hours.data

        # Convertir strings JSON a objetos Python (dict/list) si es necesario antes de guardar

        db.session.commit()

        flash('Proceso de la Hoja de Ruta actualizado exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalles del producto
        return redirect(url_for('pp.view_product', id=product.id))
    else:
        # Si hay errores de validación, flashear los errores y redirigir
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalles del producto, indicando qué modal reabrir
        return redirect(url_for('pp.view_product', id=product.id, modal=f'editProcessModal{process_id}')) # Asumiendo modales con estos IDs

# Ruta para eliminar un proceso de la Hoja de Ruta (solo POST)
@pp.route('/product_processes/delete/<int:process_id>', methods=['POST'])
@login_required
def delete_product_process(process_id):
    process = ProductProcess.query.get_or_404(process_id)
    product = process.product # Obtener el producto padre
    db.session.delete(process)
    db.session.commit()

    flash('Proceso de la Hoja de Ruta eliminado exitosamente!', 'success')
    # Redirigir de vuelta a la página de detalles del producto
    return redirect(url_for('pp.view_product', id=product.id))

# TODO: Add routes for Production Order management

# --- Rutas para Órdenes de Producción ---

# Ruta para listar órdenes de producción
@pp.route('/production_orders')
@login_required
def list_production_orders():
    # Obtener todas las órdenes de producción, cargando relaciones si es necesario (ej. con Producto)
    production_orders = ProductionOrder.query.options(joinedload(ProductionOrder.product)).all()
    # TODO: Crear plantilla list_production_orders.html
    return render_template('pp/list_production_orders.html', production_orders=production_orders)

# Ruta para crear una nueva orden de producción
@pp.route('/production_orders/new', methods=['GET', 'POST'])
@login_required
def create_production_order():
    form = ProductionOrderForm() # Crear instancia del formulario
    # TODO: Llenar SelectField de productos en el formulario
    # form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()] # Llenar SelectField

    if form.validate_on_submit():
        new_order = ProductionOrder(
            # TODO: Asignar created_by (current_user.id)
            # created_by=current_user.id,
            created_by=current_user.id, # Asignar usuario creador
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            planned_start=form.planned_start.data,
            planned_end=form.planned_end.data,
            priority=form.priority.data,
            notes=form.notes.data
            # order_number se podría generar automáticamente
        )
        db.session.add(new_order)
        db.session.commit()

        flash('Orden de Producción creada exitosamente!', 'success')
        # TODO: Redirigir a la página de detalle/edición de la OP
        return redirect(url_for('pp.list_production_orders')) # Redirigir a la lista por ahora

    # TODO: Crear plantilla add_edit_production_order.html
    return render_template('pp/add_edit_production_order.html', title='Crear Orden de Producción', form=form)

# Ruta para ver detalles de una orden de producción
@pp.route('/production_orders/<int:id>')
@login_required
def view_production_order(id):
    # Obtener la orden de producción, cargando relaciones
    order = ProductionOrder.query.options(
        joinedload(ProductionOrder.product),
        joinedload(ProductionOrder.items).joinedload(ProductionOrderItem.material),
        joinedload(ProductionOrder.processes).joinedload(ProductionProcess.operator)
    ).get_or_404(id)

    # Crear formulario para añadir un nuevo ítem
    add_item_form = ProductionOrderItemForm()
    # TODO: Llenar QuerySelectField para material en add_item_form si es necesario (query_factory ya lo hace si está bien configurado)

    # Crear formularios para editar ítems existentes
    edit_item_forms = {item.id: ProductionOrderItemForm(obj=item) for item in order.items}
    # TODO: Llenar QuerySelectField para material en cada edit_item_form si es necesario

    # Crear formulario para añadir un nuevo proceso
    add_process_form = ProductProcessForm() # type: ignore
    # TODO: Llenar QuerySelectField/SelectField en add_process_form si es necesario

    # Crear formularios para editar procesos existentes
    edit_process_forms = {process.id: ProductProcessForm(obj=process) for process in order.processes} # type: ignore
    # TODO: Llenar QuerySelectField/SelectField en cada edit_process_form si es necesario

    # TODO: Crear plantilla view_production_order.html
    return render_template('pp/view_production_order.html', 
                           order=order,
                           add_item_form=add_item_form,
                           edit_item_forms=edit_item_forms,
                           add_process_form=add_process_form,
                           edit_process_forms=edit_process_forms
                           )

# Ruta para editar una orden de producción existente
@pp.route('/production_orders/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_production_order(id):
    order = ProductionOrder.query.options(
        joinedload(ProductionOrder.product)
    ).get_or_404(id)
    form = ProductionOrderForm(obj=order) # Precargar formulario
    # TODO: Llenar SelectField de productos en el formulario (si se permite cambiar el producto)
    # form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()] # Llenar SelectField

    if form.validate_on_submit():
        # Actualizar datos de la orden
        order.product_id = form.product_id.data
        order.quantity = form.quantity.data
        order.planned_start = form.planned_start.data
        order.planned_end = form.planned_end.data
        order.priority = form.priority.data
        order.notes = form.notes.data
        # TODO: Actualizar updated_at automáticamente (en el modelo)

        db.session.commit()
        flash('Orden de Producción actualizada exitosamente!', 'success')
        # TODO: Redirigir a la página de detalle/edición de la OP
        return redirect(url_for('pp.list_production_orders')) # Redirigir a la lista por ahora

    # TODO: Crear plantilla add_edit_production_order.html
    return render_template('pp/add_edit_production_order.html', title='Editar Orden de Producción', form=form, order=order) # Pasar la orden para la plantilla

# Ruta para eliminar una orden de producción (solo POST)
@pp.route('/production_orders/delete/<int:id>', methods=['POST'])
@login_required
def delete_production_order(id):
    order = ProductionOrder.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash('Orden de Producción eliminada exitosamente!', 'success')
    return redirect(url_for('pp.list_production_orders'))

# --- Rutas para Ítems de Órdenes de Producción ---

# Ruta para añadir un nuevo ítem a una orden de producción (POST desde modal/formulario)
@pp.route('/production_orders/<int:order_id>/add_item', methods=['POST'])
@login_required
def add_production_order_item(order_id):
    order = ProductionOrder.query.get_or_404(order_id)
    form = ProductionOrderItemForm() # type: ignore # Crear instancia del formulario

    if form.validate_on_submit():
        new_item = ProductionOrderItem(
            production_order=order, # Asignar el ítem a la orden de producción
            material=form.material.data, # QuerySelectField devuelve el objeto Material
            quantity_required=form.quantity_required.data, # Usar cantidad requerida del formulario
            actual_quantity=form.actual_quantity.data or 0, # Cantidad usada puede ser 0 inicialmente
            unit_price=form.unit_price.data or 0, # Precio unitario puede ser 0 inicialmente
            notes=form.notes.data
        )
        # Calcular costo total estimado (usando quantity_required por ahora)
        new_item.total_cost = new_item.quantity_required * new_item.unit_price

        db.session.add(new_item)
        db.session.commit()

        # TODO: Recalcular el total de la orden si aplica (costo estimado) - Esto se podría hacer en la orden misma
        # order.calculate_estimated_total_cost() # Suponiendo que la orden tenga un método similar al de PurchaseOrder
        # db.session.commit()
        # Recalcular el total de la orden después de añadir un ítem
        order.calculate_estimated_total_cost()
        db.session.commit()

        flash('Ítem de Orden de Producción añadido exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalle de la orden de producción
        return redirect(url_for('pp.view_production_order', id=order.id))
    else:
        # Si hay errores de validación en el modal, flashear errores y redirigir
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalle con parámetro modal para reabrir
        # Asumimos que la plantilla view_production_order.html tiene el script para abrir modales con parámetro URL
        return redirect(url_for('pp.view_production_order', id=order.id, modal='addItemModal')) # Redirige y abre modal

# Ruta para editar un ítem de orden de producción (POST desde modal/formulario)
@pp.route('/production_order_items/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_production_order_item(item_id):
    item = ProductionOrderItem.query.get_or_404(item_id)
    order = item.production_order # Obtener la orden padre
    form = ProductionOrderItemForm(obj=item) # type: ignore # Precargar formulario

    if form.validate_on_submit():
        item.material = form.material.data
        item.quantity_required = form.quantity_required.data
        item.actual_quantity = form.actual_quantity.data or 0
        item.unit_price = form.unit_price.data or 0
        item.notes = form.notes.data

        # Recalcular costo total del ítem (usando quantity_required o actual_quantity según lógica de negocio)
        # Si el costo total en el modelo se basa en actual_quantity * unit_price, no necesitamos calcularlo aquí, solo guardar.
        # Si se basa en quantity_required * unit_price para un costo estimado, lo calculamos.
        # Basado en el modelo, total_cost es un @property, no un campo, por lo que no se guarda directamente.
        # Si necesitamos guardar un costo estimado, el modelo debería tener un campo para ello.
        # Por ahora, confiamos en la property del modelo para la visualización.

        db.session.commit()

        # TODO: Recalcular total de la orden si aplica - Esto se podría hacer en la orden misma
        # order.calculate_estimated_total_cost() # Suponiendo que la orden tenga un método similar
        # db.session.commit()
        # Recalcular el total de la orden después de editar un ítem
        order.calculate_estimated_total_cost()
        db.session.commit()

        flash('Ítem de Orden de Producción actualizado exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalle de la orden de producción
        return redirect(url_for('pp.view_production_order', id=order.id))
    else:
        # Si hay errores de validación en el modal, flashear errores y redirigir
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalle con parámetro modal para reabrir
        # Asumimos que la plantilla view_production_order.html tiene el script para abrir modales con parámetro URL
        return redirect(url_for('pp.view_production_order', id=order.id, modal=f'editItemModal{item_id}')) # Redirige y abre modal

# Ruta para eliminar un ítem de orden de producción (POST)
@pp.route('/production_order_items/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_production_order_item(item_id):
    item = ProductionOrderItem.query.get_or_404(item_id)
    order = item.production_order # Obtener la orden padre
    db.session.delete(item)
    db.session.commit()

    # TODO: Recalcular total de la orden si aplica después de eliminar
    # Recalcular el total de la orden después de eliminar un ítem
    order.calculate_estimated_total_cost()
    db.session.commit()

    flash('Ítem de Orden de Producción eliminado exitosamente!', 'success')
    # Redirigir de vuelta a la página de detalle de la orden de producción
    return redirect(url_for('pp.view_production_order', id=order.id))

# --- Rutas para Categorías de Producto ---

# Ruta para listar categorías de producto
@pp.route('/product_categories')
@login_required
def list_product_categories():
    # Obtener todas las categorías de producto
    categories = ProductCategory.query.all()
    # TODO: Crear plantilla list_product_categories.html
    return render_template('pp/list_product_categories.html', categories=categories)

# Ruta para añadir una nueva categoría de producto
@pp.route('/product_categories/new', methods=['GET', 'POST'])
@login_required
def add_product_category():
    form = ProductCategoryForm() # Crear instancia del formulario
    if form.validate_on_submit():
        # Crear y guardar nueva categoría
        new_category = ProductCategory(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            is_active=form.is_active.data
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Categoría de producto creada exitosamente!', 'success')
        return redirect(url_for('pp.list_product_categories'))
    # TODO: Crear plantilla add_edit_product_category.html
    return render_template('pp/add_edit_product_category.html', title='Añadir Nueva Categoría', form=form)

# Ruta para editar una categoría de producto existente
@pp.route('/product_categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product_category(id):
    # Obtener categoría por ID o 404
    category = ProductCategory.query.get_or_404(id)
    form = ProductCategoryForm(obj=category) # Precargar formulario

    if form.validate_on_submit():
        # Actualizar datos de la categoría y guardar
        category.name = form.name.data
        category.description = form.description.data
        category.color = form.color.data
        category.is_active = form.is_active.data
        db.session.commit()
        flash('Categoría de producto actualizada exitosamente!', 'success')
        return redirect(url_for('pp.list_product_categories'))

    # TODO: Crear plantilla add_edit_product_category.html
    return render_template('pp/add_edit_product_category.html', title='Editar Categoría', form=form)

# Ruta para eliminar una categoría de producto (solo POST)
@pp.route('/product_categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_product_category(id):
    # Obtener categoría por ID o 404 y eliminar
    category = ProductCategory.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Categoría de producto eliminada exitosamente!', 'success')
    return redirect(url_for('pp.list_product_categories'))

# --- Rutas para Hoja de Ruta Real (Procesos de Orden de Producción) ---

# Ruta para iniciar un proceso de una orden de producción
@pp.route('/production_processes/<int:process_id>/start', methods=['POST'])
@login_required
def start_production_order_process(process_id):
    process = ProductionProcess.query.get_or_404(process_id)
    order = process.production_order

    # Lógica de verificación de secuencia: un proceso solo se puede iniciar si es el primero
    # o si el proceso anterior (con sequence - 1) está completado.
    previous_process = ProductionProcess.query.filter_by(
        production_order=order,
        sequence=process.sequence - 1
    ).first()

    if previous_process and previous_process.status != 'completed':
        flash(f'No se puede iniciar el proceso \'{process.process_type}\' (Secuencia {process.sequence}). El proceso anterior (Secuencia {previous_process.sequence}) aún no ha sido completado.', 'warning')
    elif process.status == 'pending':
        # Usar el método update_status del modelo si existe y maneja la fecha
        # if process.update_status('in_progress'): # Asumiendo que el modelo tiene este método
        process.status = 'in_progress'
        process.start_date = datetime.utcnow()
        db.session.commit()
        flash(f'Proceso \'{process.process_type}\' iniciado.', 'success')
        # Actualizar el estado de la orden después de iniciar un proceso
        order.update_order_status_from_processes()
        db.session.commit()
    else:
        flash(f'No se puede iniciar el proceso \'{process.process_type}\' en estado {process.status}.', 'warning')

    return redirect(url_for('pp.view_production_order', id=order.id))

# Ruta para completar un proceso de una orden de producción
@pp.route('/production_processes/<int:process_id>/complete', methods=['POST'])
@login_required
def complete_production_order_process(process_id):
    process = ProductionProcess.query.get_or_404(process_id)
    order = process.production_order

    # Verificar si el proceso está en un estado que permite completarlo
    if process.status == 'in_progress':
        # if process.update_status('completed'): # Asumiendo que el modelo tiene este método
        process.status = 'completed'
        process.end_date = datetime.utcnow()
        # TODO: Capturar actual_hours, operator_id si no se hizo antes
        db.session.commit()
        flash(f'Proceso \'{process.process_type}\' completado.', 'success')
        # TODO: Lógica para actualizar el estado de la Orden de Producción si todos los procesos están completos
        # Actualizar el estado de la orden después de completar un proceso
        order.update_order_status_from_processes()
        db.session.commit()
    else:
        flash(f'No se puede completar el proceso \'{process.process_type}\' en estado {process.status}.', 'warning')

    return redirect(url_for('pp.view_production_order', id=order.id))

# Ruta para cancelar un proceso de una orden de producción
@pp.route('/production_processes/<int:process_id>/cancel', methods=['POST'])
@login_required
def cancel_production_order_process(process_id):
    process = ProductionProcess.query.get_or_404(process_id)
    order = process.production_order

    # Verificar si el proceso está en un estado que permite cancelarlo
    if process.status in ['pending', 'in_progress']:
        # if process.update_status('cancelled'): # Podríamos añadir un estado 'cancelled' al modelo Process si es útil
        # Por ahora, lo marcaremos con un estado específico o notas
        process.status = 'cancelled' # Asumiendo que añadimos 'cancelled' a los estados posibles en el modelo
        # TODO: Añadir motivo de cancelación
        db.session.commit()
        flash(f'Proceso \'{process.process_type}\' cancelado.', 'success')
        # Actualizar el estado de la orden después de cancelar un proceso
        order.update_order_status_from_processes()
        db.session.commit()
    else:
        flash(f'No se puede cancelar el proceso \'{process.process_type}\' en estado {process.status}.', 'warning')

    return redirect(url_for('pp.view_production_order', id=order.id))

# TODO: Rutas para asignar operador y registrar horas reales si se hace por separado

# TODO: Add PP routes here 