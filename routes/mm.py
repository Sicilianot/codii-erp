from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user # Importar current_user
from app import db # Importar la instancia de SQLAlchemy
from models.all_models import Material, Supplier, PurchaseOrder, PurchaseOrderItem, MaterialCategory, MaterialMovement # Actualizada la importación de modelos
from app.forms.mm import MaterialForm, SupplierForm, PurchaseOrderForm, PurchaseOrderItemForm, MaterialCategoryForm, MaterialMovementForm # Importar los formularios
from sqlalchemy.orm import joinedload # Para cargar la relación con Supplier
from decimal import Decimal # Necesario para cálculos con DecimalFields
from datetime import datetime

mm = Blueprint('mm', __name__, url_prefix='/mm')

# Función auxiliar para recalcular el monto total de una OC
def calculate_purchase_order_total(order):
    total = Decimal('0.00')
    for item in order.items:
        total += item.quantity * item.unit_price
    order.total_amount = total
    db.session.commit()

# Ruta para listar materiales
@mm.route('/materials')
@login_required # Proteger esta ruta
def list_materials():
    materials = Material.query.all() # Obtener todos los materiales de la base de datos
    return render_template('mm/list_materials.html', materials=materials)

# Ruta para añadir un nuevo material
@mm.route('/materials/new', methods=['GET', 'POST'])
@login_required # Proteger esta ruta
def add_material():
    form = MaterialForm() # Crear una instancia del formulario
    if form.validate_on_submit(): # Si el formulario se envía y es válido
        # Crear un nuevo objeto Material con los datos del formulario
        new_material = Material(
            name=form.name.data,
            description=form.description.data,
            unit=form.unit.data,
            current_stock=form.initial_stock.data # Asigna el stock inicial como stock actual
        )
        db.session.add(new_material) # Añadir el nuevo material a la sesión de la base de datos
        db.session.commit() # Guardar los cambios en la base de datos
        flash('Material creado exitosamente!', 'success') # Mostrar mensaje de éxito
        return redirect(url_for('mm.list_materials')) # Redirigir a la lista de materiales

    # Si la solicitud es GET o el formulario no es válido, renderizar la plantilla con el formulario
    return render_template('mm/add_edit_material.html', title='Añadir Nuevo Material', form=form)

# Ruta para editar un material existente
@mm.route('/materials/edit/<int:id>', methods=['GET', 'POST'])
@login_required # Proteger esta ruta
def edit_material(id):
    material = Material.query.get_or_404(id) # Obtener el material por ID o mostrar 404 si no existe
    form = MaterialForm(obj=material) # Crear instancia del formulario, precargado con datos del material

    if form.validate_on_submit(): # Si el formulario se envía y es válido
        # Actualizar los datos del material con los del formulario
        material.name = form.name.data
        material.description = form.description.data
        material.unit = form.unit.data
        # El stock actual no se actualiza desde este formulario de edición

        db.session.commit() # Guardar los cambios
        flash('Material actualizado exitosamente!', 'success') # Mensaje de éxito
        return redirect(url_for('mm.list_materials')) # Redirigir a la lista

    # Si es GET o formulario inválido, renderizar la plantilla con el formulario precargado
    return render_template('mm/add_edit_material.html', title='Editar Material', form=form)

# Ruta para eliminar un material (solo POST para seguridad)
@mm.route('/materials/delete/<int:id>', methods=['POST'])
@login_required # Proteger esta ruta
def delete_material(id):
    material = Material.query.get_or_404(id) # Obtener el material o 404
    db.session.delete(material) # Eliminar el material
    db.session.commit() # Guardar cambios
    flash('Material eliminado exitosamente!', 'success') # Mensaje de éxito
    return redirect(url_for('mm.list_materials')) # Redirigir a la lista

# Ruta para listar proveedores
@mm.route('/suppliers')
@login_required # Proteger esta ruta
def list_suppliers():
    suppliers = Supplier.query.all() # Obtener todos los proveedores
    return render_template('mm/list_suppliers.html', suppliers=suppliers)

# Ruta para añadir un nuevo proveedor
@mm.route('/suppliers/new', methods=['GET', 'POST'])
@login_required # Proteger esta ruta
def add_supplier():
    form = SupplierForm() # Crear instancia del formulario
    if form.validate_on_submit(): # Si el formulario es válido
        new_supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            notes=form.notes.data
        )
        db.session.add(new_supplier) # Añadir a la sesión
        db.session.commit() # Guardar cambios
        flash('Proveedor creado exitosamente!', 'success') # Mensaje
        return redirect(url_for('mm.list_suppliers')) # Redirigir a la lista

    # Si es GET o formulario inválido, renderizar la plantilla
    return render_template('mm/add_edit_supplier.html', title='Añadir Nuevo Proveedor', form=form)

# Ruta para editar un proveedor existente
@mm.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
@login_required # Proteger esta ruta
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id) # Obtener proveedor o 404
    form = SupplierForm(obj=supplier) # Instancia del formulario precargado

    if form.validate_on_submit(): # Si el formulario es válido
        # Actualizar datos del proveedor
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data
        supplier.notes = form.notes.data

        db.session.commit() # Guardar cambios
        flash('Proveedor actualizado exitosamente!', 'success') # Mensaje
        return redirect(url_for('mm.list_suppliers')) # Redirigir a la lista

    # Si es GET o formulario inválido, renderizar la plantilla precargada
    return render_template('mm/add_edit_supplier.html', title='Editar Proveedor', form=form)

# Ruta para eliminar un proveedor (solo POST)
@mm.route('/suppliers/delete/<int:id>', methods=['POST'])
@login_required # Proteger esta ruta
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id) # Obtener proveedor o 404
    db.session.delete(supplier) # Eliminar proveedor
    db.session.commit() # Guardar cambios
    flash('Proveedor eliminado exitosamente!', 'success') # Mensaje
    return redirect(url_for('mm.list_suppliers')) # Redirigir a la lista

# Ruta para listar órdenes de compra
@mm.route('/purchase_orders')
@login_required
def list_purchase_orders():
    # Cargar las órdenes de compra y los proveedores relacionados para evitar consultas N+1
    purchase_orders = PurchaseOrder.query.options(joinedload(PurchaseOrder.supplier)).all()
    return render_template('mm/list_purchase_orders.html', purchase_orders=purchase_orders)

# Ruta para crear una nueva orden de compra
@mm.route('/purchase_orders/new', methods=['GET', 'POST'])
@login_required
def create_purchase_order():
    form = PurchaseOrderForm() # Crear instancia del formulario
    if form.validate_on_submit():
        new_order = PurchaseOrder(
            supplier=form.supplier.data, # supplier es un objeto Supplier gracias a QuerySelectField
            order_date=form.order_date.data,
            status=form.status.data,
            notes=form.notes.data
            # total_amount se calcularía en base a los ítems, lo dejamos en 0 por ahora
        )
        db.session.add(new_order)
        db.session.commit() # Primero guardamos la orden para tener un ID si necesitamos añadir ítems después

        # TODO: Implementar lógica para añadir ítems a la orden de compra

        flash('Orden de Compra creada exitosamente!', 'success')
        # TODO: Redirigir a la página de detalle/edición de la OC para añadir ítems
        return redirect(url_for('mm.list_purchase_orders')) # Redirigimos a la lista por ahora

    # TODO: Crear plantilla add_edit_purchase_order.html
    return render_template('mm/add_edit_purchase_order.html', title='Crear Orden de Compra', form=form)

# Ruta para ver detalles de una orden de compra
@mm.route('/purchase_orders/<int:id>')
@login_required
def view_purchase_order(id):
    # Cargar la orden de compra y sus ítems, así como el proveedor
    order = PurchaseOrder.query.options(joinedload(PurchaseOrder.supplier), joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.material)).get_or_404(id)
    # TODO: Crear plantilla view_purchase_order.html
    return render_template('mm/view_purchase_order.html', order=order)

# Ruta para editar una orden de compra existente
@mm.route('/purchase_orders/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_purchase_order(id):
    # Cargar la orden de compra y sus ítems
    order = PurchaseOrder.query.options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.items)
    ).get_or_404(id)

    form = PurchaseOrderForm(obj=order) # Precargar formulario de la orden principal
    add_item_form = PurchaseOrderItemForm() # Formulario para añadir nuevos ítems

    # Crear formularios precargados para cada ítem existente
    item_forms = []
    for item in order.items:
        # Crear una instancia del formulario de ítem para cada item y precargarla
        item_form = PurchaseOrderItemForm(obj=item)
        # Necesitamos pasar el item.id al formulario para la ruta de edición
        # Aunque no es un campo del modelo, lo podemos asignar dinámicamente para usarlo en el action del form
        item_form.id = item.id # type: ignore # Añadir el ID del ítem al formulario
        item_forms.append(item_form)

    if form.validate_on_submit():
        # Actualizar datos de la orden
        order.supplier = form.supplier.data
        order.order_date = form.order_date.data
        order.status = form.status.data
        order.notes = form.notes.data
        # total_amount y ítems se manejan por separado

        db.session.commit()
        flash('Orden de Compra actualizada exitosamente!', 'success')
        # TODO: Redirigir a la página de detalle/edición de la OC
        return redirect(url_for('mm.edit_purchase_order', id=order.id)) # Redirigimos a la misma página de edición

    # Si es GET o formulario inválido, renderizar la plantilla precargada
    # Pasar la orden, el formulario de la orden, el formulario para añadir ítems,
    # y la lista de formularios para editar ítems
    return render_template(
        'mm/add_edit_purchase_order.html',
        title='Editar Orden de Compra',
        form=form, # Formulario de la orden principal
        order=order, # Objeto de la orden
        add_item_form=add_item_form, # Formulario para añadir nuevos ítems
        item_forms=item_forms # Lista de formularios precargados para ítems existentes
    )

# Ruta para cancelar una orden de compra
@mm.route('/purchase_orders/cancel/<int:id>', methods=['POST'])
@login_required
def cancel_purchase_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    # Solo permitir cancelar si está pendiente o aprobada
    if order.status in ['pending', 'approved']:
        order.status = 'cancelled'
        # TODO: Implementar lógica de reversión si es necesario (ej: si ya afectó inventario)
        db.session.commit()
        flash('Orden de Compra cancelada.', 'success')
    else:
        flash(f'No se puede cancelar una orden en estado {order.status}.', 'warning')

    return redirect(url_for('mm.list_purchase_orders')) # Redirigir a la lista

# Ruta para añadir un nuevo ítem a una orden de compra (POST desde modal/formulario)
@mm.route('/purchase_orders/<int:order_id>/add_item', methods=['POST'])
@login_required
def add_purchase_order_item(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    form = PurchaseOrderItemForm() # type: ignore
    # Al usar WTForms, validate_on_submit() verifica tanto POST como validadores
    if form.validate_on_submit():
        new_item = PurchaseOrderItem(
            order=order, # Asignar el ítem a la orden
            material=form.material.data, # QuerySelectField devuelve el objeto
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            # subtotal se calculará en el modelo o antes de guardar
        )
        # Calcular subtotal antes de añadir (o definir un event listener en SQLAlchemy)
        new_item.subtotal = new_item.quantity * new_item.unit_price
        db.session.add(new_item)
        db.session.commit()

        # Recalcular total de la orden
        calculate_purchase_order_total(order)

        flash('Ítem añadido exitosamente!', 'success')
        # Redirigir de vuelta a la página de edición de la orden principal
        return redirect(url_for('mm.edit_purchase_order', id=order.id))
    else:
         # Si hay errores de validación en el modal:
         # 1. Flashear los errores específicos
         # 2. Redirigir de vuelta a la página de edición, indicando qué modal tenía errores
         for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

         # Redirigir de vuelta a la página de edición, con un parámetro para abrir el modal
         return redirect(url_for('mm.edit_purchase_order', id=order.id, modal='addItemModal'))

# Ruta para editar un ítem de orden de compra (POST desde modal/formulario)
@mm.route('/purchase_order_items/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_purchase_order_item(item_id):
    item = PurchaseOrderItem.query.get_or_404(item_id)
    order = item.order # Obtener la orden padre
    form = PurchaseOrderItemForm(obj=item) # type: ignore

    if form.validate_on_submit():
        item.material = form.material.data
        item.quantity = form.quantity.data
        item.unit_price = form.unit_price.data
        # Recalcular subtotal
        item.subtotal = item.quantity * item.unit_price

        db.session.commit()

        # Recalcular total de la orden
        calculate_purchase_order_total(order)

        flash('Ítem actualizado exitosamente!', 'success')
        # Redirigir de vuelta a la página de edición de la orden principal
        return redirect(url_for('mm.edit_purchase_order', id=order.id))
    else:
        # Si hay errores de validación en el modal:
        # 1. Flashear los errores específicos
        # 2. Redirigir de vuelta a la página de edición, indicando qué modal tenía errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de edición, con un parámetro para abrir el modal de este ítem
        return redirect(url_for('mm.edit_purchase_order', id=order.id, modal=f'editItemModal{item_id}'))

# Ruta para eliminar un ítem de orden de compra (POST)
@mm.route('/purchase_order_items/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_purchase_order_item(item_id):
    item = PurchaseOrderItem.query.get_or_404(item_id)
    order = item.order # Obtener la orden padre
    db.session.delete(item)
    db.session.commit()

    # Recalcular total de la orden después de eliminar
    calculate_purchase_order_total(order)

    flash('Ítem eliminado exitosamente!', 'success')
    # Redirigir de vuelta a la página de detalle/edición de la orden
    return redirect(url_for('mm.view_purchase_order', id=order.id))

# --- Rutas para Categorías de Materiales ---

# Ruta para listar categorías de materiales
@mm.route('/material_categories')
@login_required
def list_material_categories():
    # Obtener todas las categorías de materiales de la base de datos
    categories = MaterialCategory.query.all()

    # Determinar el color del texto para cada categoría basado en el color de fondo
    for category in categories:
        # Lógica para determinar si el color de fondo es claro u oscuro
        # Una heurística simple es convertir el color hexadecimal a valores RGB y calcular la luminosidad percibida.
        # Si la luminosidad es alta, usar texto oscuro (#000000); si es baja, usar texto claro (#ffffff).
        # Esto es una aproximación, una librería front-end o una función JS sería más precisa.
        # Para simplificar aquí, solo verificaremos algunos colores muy claros como antes.
        if category.color and category.color.lower() in ['#ffffff', '#fffffe', '#fffff9']:
            category.text_color = '#000000'
        else:
            category.text_color = '#ffffff'

    # TODO: Crear plantilla list_material_categories.html
    return render_template('mm/list_material_categories.html', categories=categories)

# Ruta para añadir una nueva categoría de material
@mm.route('/material_categories/new', methods=['GET', 'POST'])
@login_required
def add_material_category():
    form = MaterialCategoryForm() # type: ignore # Crear instancia del formulario
    if form.validate_on_submit():
        # Crear y guardar nueva categoría
        new_category = MaterialCategory(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            is_active=form.is_active.data
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Categoría de material creada exitosamente!', 'success')
        return redirect(url_for('mm.list_material_categories'))
    # TODO: Crear plantilla add_edit_material_category.html
    return render_template('mm/add_edit_material_category.html', title='Añadir Nueva Categoría', form=form)

# Ruta para editar una categoría de material existente
@mm.route('/material_categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_material_category(id):
    # Obtener categoría por ID o 404
    category = MaterialCategory.query.get_or_404(id)
    form = MaterialCategoryForm(obj=category) # type: ignore # Precargar formulario

    if form.validate_on_submit():
        # Actualizar datos de la categoría y guardar
        category.name = form.name.data
        category.description = form.description.data
        category.color = form.color.data
        category.is_active = form.is_active.data
        db.session.commit()
        flash('Categoría de material actualizada exitosamente!', 'success')
        return redirect(url_for('mm.list_material_categories'))

    # TODO: Crear plantilla add_edit_material_category.html
    return render_template('mm/add_edit_material_category.html', title='Editar Categoría', form=form)

# Ruta para eliminar una categoría de material (solo POST)
@mm.route('/material_categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_material_category(id):
    # Obtener categoría por ID o 404 y eliminar
    category = MaterialCategory.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Categoría de material eliminada exitosamente!', 'success')
    return redirect(url_for('mm.list_material_categories'))

# --- Rutas para Movimientos de Materiales ---

# Ruta para listar movimientos de materiales
@mm.route('/material_movements')
@login_required
def list_material_movements():
    # Obtener todos los movimientos de materiales, cargando la relación con Material para mostrar el nombre
    movements = MaterialMovement.query.options(joinedload(MaterialMovement.material)).all() # type: ignore
    # TODO: Crear plantilla list_material_movements.html
    return render_template('mm/list_material_movements.html', movements=movements)

# Ruta para ver detalles de un material
@mm.route('/materials/<int:id>')
@login_required
def view_material(id):
    material = Material.query.options(joinedload(Material.movements).joinedload(MaterialMovement.user)).get_or_404(id)
    movement_form = MaterialMovementForm() # Formulario para añadir movimientos desde esta página
    # TODO: Crear plantilla view_material.html
    return render_template('mm/view_material.html', material=material, movement_form=movement_form)

# Ruta para añadir un nuevo movimiento de material (generalmente desde la página de un material específico)
@mm.route('/materials/<int:material_id>/add_movement', methods=['POST'])
@login_required
def add_material_movement(material_id):
    material = Material.query.get_or_404(material_id)
    form = MaterialMovementForm() # type: ignore # Crear instancia del formulario

    if form.validate_on_submit():
        # TODO: Considerar validación para stock negativo si aplica
        if form.adjustment_type.data == 'out' and form.quantity.data > material.current_stock:
            flash('Error: La cantidad de salida excede el stock actual.', 'danger')
            return redirect(url_for('mm.view_material', id=material.id))

        # Crear y guardar nuevo movimiento
        new_movement = MaterialMovement(
            material=material, # Asignar el movimiento al material
            adjustment_type=form.adjustment_type.data,
            quantity=form.quantity.data,
            notes=form.notes.data
            # TODO: Agregar user_id y date automáticamente
        )
        # TODO: Obtener el usuario actual y la fecha/hora
        # Asumiendo que current_user está disponible y MaterialMovement tiene un campo date
        # new_movement.user_id = current_user.id
        # new_movement.date = datetime.utcnow()

        # Asignar el usuario actual y la fecha al movimiento
        new_movement.user_id = current_user.id
        new_movement.date = datetime.utcnow()

        db.session.add(new_movement)

        # Actualizar el stock actual del material
        if new_movement.adjustment_type == 'in':
            material.current_stock += new_movement.quantity
        elif new_movement.adjustment_type == 'out':
            material.current_stock -= new_movement.quantity

        db.session.commit()

        flash('Movimiento de material registrado exitosamente!', 'success')
        # Redirigir de vuelta a la página de detalle del material (asumiendo que existe)
        # TODO: Crear ruta y plantilla para ver detalle de material si aún no existe
        return redirect(url_for('mm.view_material', id=material.id)) # Asumiendo una ruta view_material
    else:
        # Si hay errores de validación, flashear los errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')

        # Redirigir de vuelta a la página de detalle del material
        return redirect(url_for('mm.view_material', id=material.id)) # Asumiendo una ruta view_material

# TODO: Considerar cómo manejar los movimientos de inventario relacionados con Órdenes de Compra (recepción).
# TODO: Asegurar que los modelos están importados correctamente en app/models/mm/__init__.py
# TODO: Registrar este Blueprint en la instancia principal de la aplicación Flask (__init__.py o app.py).
# TODO: Implementar los modales en las plantillas view_purchase_order.html y add_edit_purchase_order.html para añadir/editar ítems.