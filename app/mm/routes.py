from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Material, MaterialMovement, MaterialCategory
from app.forms.mm import MaterialForm, MaterialMovementForm
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('mm', __name__, url_prefix='/mm')

@bp.route('/inventory')
@login_required
def inventory():
    # Obtener parámetros de filtrado
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    stock_status = request.args.get('stock_status', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Construir query base
    query = Material.query

    # Aplicar filtros
    if search:
        query = query.filter(
            (Material.code.ilike(f'%{search}%')) |
            (Material.name.ilike(f'%{search}%'))
        )
    
    if category_id:
        query = query.filter(Material.category_id == category_id)
    
    if stock_status:
        if stock_status == 'low':
            query = query.filter(Material.current_stock <= Material.min_stock)
        elif stock_status == 'out':
            query = query.filter(Material.current_stock == 0)
        elif stock_status == 'normal':
            query = query.filter(Material.current_stock > Material.min_stock)
    
    if status:
        query = query.filter(Material.is_active == (status == 'active'))

    # Obtener datos para KPIs
    total_materials = Material.query.count()
    total_stock = db.session.query(func.sum(Material.current_stock)).scalar() or 0
    low_stock_count = Material.query.filter(Material.current_stock <= Material.min_stock).count()
    total_value = db.session.query(
        func.sum(Material.current_stock * Material.unit_price)
    ).scalar() or 0

    # Obtener materiales paginados
    materials = query.order_by(Material.name).paginate(page=page, per_page=per_page)

    # Obtener categorías para el filtro
    categories = MaterialCategory.query.order_by(MaterialCategory.name).all()

    # Crear formularios para ajustes de stock
    adjust_forms = {}
    for material in materials.items:
        form = MaterialMovementForm()
        form.material_id.data = material.id
        adjust_forms[material.id] = form

    return render_template('mm/inventory.html',
                         materials=materials,
                         categories=categories,
                         adjust_forms=adjust_forms,
                         total_materials=total_materials,
                         total_stock=total_stock,
                         low_stock_count=low_stock_count,
                         total_value=total_value)

@bp.route('/adjust_stock', methods=['POST'])
@login_required
def adjust_stock():
    form = MaterialMovementForm()
    if form.validate_on_submit():
        material = Material.query.get_or_404(form.material_id.data)
        
        # Crear movimiento
        movement = MaterialMovement(
            material_id=material.id,
            type=form.adjustment_type.data,
            quantity=form.quantity.data,
            notes=form.notes.data,
            user_id=current_user.id,
            date=datetime.utcnow()
        )

        # Actualizar stock
        if form.adjustment_type.data == 'in':
            material.current_stock += form.quantity.data
        else:  # out
            if material.current_stock < form.quantity.data:
                flash('No hay suficiente stock disponible.', 'danger')
                return redirect(url_for('mm.inventory'))
            material.current_stock -= form.quantity.data

        # Guardar movimiento y actualizar material
        db.session.add(movement)
        db.session.commit()

        flash('Ajuste de stock realizado con éxito.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('mm.inventory'))

@bp.route('/material/<int:id>')
@login_required
def view_material(id):
    material = Material.query.get_or_404(id)
    movements = MaterialMovement.query.filter_by(material_id=id)\
        .order_by(MaterialMovement.date.desc())\
        .limit(10)\
        .all()
    
    return render_template('mm/material_detail.html',
                         material=material,
                         movements=movements)

@bp.route('/material/movements/<int:id>')
@login_required
def material_movements(id):
    material = Material.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    movements = MaterialMovement.query.filter_by(material_id=id)\
        .order_by(MaterialMovement.date.desc())\
        .paginate(page=page, per_page=per_page)

    return render_template('mm/material_movements.html',
                         material=material,
                         movements=movements)

@bp.route('/inventory/report')
@login_required
def inventory_report():
    # Obtener parámetros de filtrado
    category_id = request.args.get('category', type=int)
    stock_status = request.args.get('stock_status', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')

    # Construir query base
    query = Material.query

    # Aplicar filtros
    if search:
        query = query.filter(
            (Material.code.ilike(f'%{search}%')) |
            (Material.name.ilike(f'%{search}%')) |
            (Material.description.ilike(f'%{search}%'))
        )
    
    if category_id:
        query = query.filter(Material.category_id == category_id)
    
    if stock_status:
        if stock_status == 'low':
            query = query.filter(Material.current_stock <= Material.min_stock)
        elif stock_status == 'out':
            query = query.filter(Material.current_stock == 0)
        elif stock_status == 'normal':
            query = query.filter(Material.current_stock > Material.min_stock)

    # Aplicar ordenamiento
    if sort_by == 'name':
        query = query.order_by(Material.name.asc() if sort_order == 'asc' else Material.name.desc())
    elif sort_by == 'code':
        query = query.order_by(Material.code.asc() if sort_order == 'asc' else Material.code.desc())
    elif sort_by == 'stock':
        query = query.order_by(Material.current_stock.asc() if sort_order == 'asc' else Material.current_stock.desc())
    elif sort_by == 'value':
        query = query.order_by((Material.current_stock * Material.unit_price).asc() if sort_order == 'asc' 
                             else (Material.current_stock * Material.unit_price).desc())

    # Obtener materiales
    materials = query.all()

    # Calcular totales
    total_materials = len(materials)
    total_stock = sum(m.current_stock for m in materials)
    total_value = sum(m.total_value for m in materials)
    low_stock_count = sum(1 for m in materials if m.current_stock <= m.min_stock)

    # Obtener categorías para el filtro
    categories = MaterialCategory.query.order_by(MaterialCategory.name).all()

    # Preparar datos para el reporte
    report_data = {
        'materials': materials,
        'categories': categories,
        'total_materials': total_materials,
        'total_stock': total_stock,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'current_filters': {
            'category': category_id,
            'stock_status': stock_status,
            'search': search,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    }

    return render_template('mm/inventory_report.html', **report_data) 