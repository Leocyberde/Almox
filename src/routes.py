import os
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from models import brazil_now
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Product, Allocation, StockMovement
from forms import (LoginForm, ForgotPasswordForm, ResetPasswordForm, EmployeeForm, 
                   EditEmployeeForm, ProductForm, AllocationForm, StockAdjustmentForm,
                   ProductionRequestForm, ApprovalForm)
from utils import save_uploaded_file, delete_uploaded_file, generate_reset_token, send_reset_email, log_stock_movement

# Authentication routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'almoxarifado':
            return redirect(url_for('dashboard_almoxarifado'))
        else:
            return redirect(url_for('dashboard_producao'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos, ou conta desativada.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_reset_token()
            user.reset_token = token
            user.reset_token_expires = brazil_now() + timedelta(hours=1)
            db.session.commit()
            
            if send_reset_email(user, token):
                flash('Instruções para redefinir sua senha foram enviadas para seu email.', 'info')
            else:
                flash('Erro ao enviar email. Tente novamente mais tarde.', 'danger')
        else:
            flash('Email não encontrado.', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    if not token:
        flash('Token inválido.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < brazil_now():
        flash('Token inválido ou expirado.', 'danger')
        return redirect(url_for('login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash('Sua senha foi redefinida com sucesso.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form)

# Dashboard routes
@app.route('/dashboard/almoxarifado')
@login_required
def dashboard_almoxarifado():
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard_producao'))
    
    # Statistics
    total_products = Product.query.count()
    total_allocations = Allocation.query.count()
    low_stock_products = Product.query.filter(Product.quantity <= 10).count()
    pending_requests = Allocation.query.filter_by(status='pending').count()
    recent_allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).limit(5).all()
    
    return render_template('dashboard_almoxarifado.html', 
                         total_products=total_products,
                         total_allocations=total_allocations,
                         low_stock_products=low_stock_products,
                         pending_requests=pending_requests,
                         recent_allocations=recent_allocations)

@app.route('/dashboard/producao')
@login_required
def dashboard_producao():
    # Statistics for production users
    total_requests = Allocation.query.filter_by(user_id=current_user.id).count()
    pending_requests = Allocation.query.filter_by(user_id=current_user.id, status='pending').count()
    approved_requests = Allocation.query.filter_by(user_id=current_user.id, status='approved').count()
    rejected_requests = Allocation.query.filter_by(user_id=current_user.id, status='rejected').count()
    recent_user_allocations = Allocation.query.filter_by(user_id=current_user.id).order_by(Allocation.allocated_at.desc()).limit(10).all()
    
    return render_template('dashboard_producao.html',
                         total_requests=total_requests,
                         pending_requests=pending_requests,
                         approved_requests=approved_requests,
                         rejected_requests=rejected_requests,
                         recent_allocations=recent_user_allocations)

# Product management routes
@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard_producao'))
    
    form = ProductForm()
    if form.validate_on_submit():
        try:
            # Save uploaded photo
            photo_filename = None
            if form.photo.data and form.photo.data.filename:
                photo_filename = save_uploaded_file(form.photo.data)
                if not photo_filename:
                    flash('Erro ao salvar a foto. Verifique se o arquivo é uma imagem válida (JPG, PNG, GIF).', 'danger')
                    return render_template('add_product.html', form=form)
            
            product = Product(
                code=form.code.data,
                name=form.name.data,
                supplier_reference=form.supplier_reference.data,
                location=form.location.data,
                quantity=0,  # Start with 0, then add via stock movement
                unit=form.unit.data,
                supplier_name=form.supplier_name.data,
                photo_filename=photo_filename,
                created_by=current_user.id
            )
            
            db.session.add(product)
            db.session.commit()
            
            # Log initial stock
            log_stock_movement(product, current_user, 'add', form.quantity.data, 'Produto cadastrado')
            db.session.commit()
            
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('manage_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar produto: {e}")
            flash('Erro interno do servidor. Tente novamente.', 'danger')
            return render_template('add_product.html', form=form)
    
    return render_template('add_product.html', form=form)

@app.route('/products/manage')
@login_required
def manage_products():
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard_producao'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Product.query
    if search:
        query = query.filter(
            Product.name.contains(search) | 
            Product.code.contains(search) |
            Product.supplier_reference.contains(search)
        )
    
    products = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Create form for CSRF token in stock adjustment modals
    form = StockAdjustmentForm()
    
    return render_template('manage_products.html', products=products, search=search, form=form)

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard_producao'))
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.product_id = product.id  # For validation
    
    if form.validate_on_submit():
        # Handle photo update
        if form.photo.data:
            # Delete old photo
            if product.photo_filename:
                delete_uploaded_file(product.photo_filename)
            # Save new photo
            product.photo_filename = save_uploaded_file(form.photo.data)
        
        product.code = form.code.data
        product.name = form.name.data
        product.supplier_reference = form.supplier_reference.data
        product.location = form.location.data
        product.unit = form.unit.data
        product.supplier_name = form.supplier_name.data
        product.updated_at = brazil_now()
        
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('edit_product.html', form=form, product=product)

@app.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'almoxarifado' or not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manage_products'))
    
    product = Product.query.get_or_404(product_id)
    
    # Check if product has allocations
    if product.allocations:
        flash('Não é possível excluir produto com alocações associadas.', 'danger')
        return redirect(url_for('manage_products'))
    
    # Delete photo file
    if product.photo_filename:
        delete_uploaded_file(product.photo_filename)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('manage_products'))

@app.route('/products/<int:product_id>/adjust_stock', methods=['POST'])
@login_required
def adjust_stock(product_id):
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manage_products'))
    
    product = Product.query.get_or_404(product_id)
    form = StockAdjustmentForm()
    
    if form.validate_on_submit():
        log_stock_movement(
            product, 
            current_user, 
            form.adjustment_type.data, 
            form.quantity.data, 
            form.notes.data
        )
        db.session.commit()
        
        flash('Estoque ajustado com sucesso!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('manage_products'))

# Employee management routes
@app.route('/employees/manage')
@login_required
def manage_employees():
    if current_user.role != 'almoxarifado' or not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    employees = User.query.all()
    return render_template('manage_employees.html', employees=employees)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if current_user.role != 'almoxarifado' or not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    form = EmployeeForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Nome de usuário já existe.', 'danger')
            return render_template('add_employee.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'danger')
            return render_template('add_employee.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_admin=form.is_admin.data,
            created_by=current_user.id
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Funcionário adicionado com sucesso!', 'success')
        return redirect(url_for('manage_employees'))
    
    return render_template('add_employee.html', form=form)

@app.route('/employees/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(user_id):
    if current_user.role != 'almoxarifado' or not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    form = EditEmployeeForm(obj=user)
    
    if form.validate_on_submit():
        # Check if username or email already exists (excluding current user)
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user and existing_user.id != user.id:
            flash('Nome de usuário já existe.', 'danger')
            return render_template('edit_employee.html', form=form, user=user)
        
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != user.id:
            flash('Email já cadastrado.', 'danger')
            return render_template('edit_employee.html', form=form, user=user)
        
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('manage_employees'))
    
    return render_template('edit_employee.html', form=form, user=user)

@app.route('/employees/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_employee(user_id):
    if current_user.role != 'almoxarifado' or not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('manage_employees'))
    
    if user_id == current_user.id:
        flash('Você não pode excluir sua própria conta.', 'danger')
        return redirect(url_for('manage_employees'))
    
    user = User.query.get_or_404(user_id)
    
    # Check if user has allocations
    if user.allocations:
        flash('Não é possível excluir usuário com alocações associadas.', 'danger')
        return redirect(url_for('manage_employees'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('Funcionário excluído com sucesso!', 'success')
    return redirect(url_for('manage_employees'))

# Allocation routes
@app.route('/allocate', methods=['GET', 'POST'])
@login_required
def allocate_product():
    # Use different forms for different roles
    if current_user.role == 'producao':
        return redirect(url_for('request_product'))
    
    form = AllocationForm()
    
    # Pre-select product if product_id is provided in URL
    product_id = request.args.get('product_id', type=int)
    selected_product = None
    if product_id:
        selected_product = Product.query.get(product_id)
        if selected_product:
            form.product_search.data = f"{selected_product.code} - {selected_product.name}"
            form.product_id.data = str(selected_product.id)
    
    if form.validate_on_submit():
        product = Product.query.get_or_404(form.product_id.data)
        
        if product.quantity < form.quantity.data:
            flash('Quantidade insuficiente em estoque.', 'danger')
            return render_template('allocate_product.html', form=form, selected_product=selected_product)
        
        allocation = Allocation(
            product_id=product.id,
            user_id=current_user.id,
            work_number=form.work_number.data,
            quantity=form.quantity.data,
            notes=form.notes.data,
            status='approved',  # Direct allocation for warehouse staff
            approved_by_id=current_user.id,
            approved_at=brazil_now()
        )
        
        db.session.add(allocation)
        
        # Update stock
        log_stock_movement(
            product, 
            current_user, 
            'allocation', 
            form.quantity.data, 
            f'Alocado para obra {form.work_number.data}'
        )
        
        db.session.commit()
        
        flash('Produto alocado com sucesso!', 'success')
        return redirect(url_for('allocation_history'))
    
    return render_template('allocate_product.html', form=form, selected_product=selected_product)

# New route for production users to request allocations
@app.route('/request', methods=['GET', 'POST'])
@login_required
def request_product():
    if current_user.role != 'producao':
        flash('Acesso negado. Esta página é apenas para usuários de produção.', 'danger')
        return redirect(url_for('index'))
    
    form = ProductionRequestForm()
    
    # Pre-select product if product_id is provided in URL
    product_id = request.args.get('product_id', type=int)
    selected_product = None
    if product_id:
        selected_product = Product.query.get(product_id)
        if selected_product:
            form.product_search.data = f"{selected_product.code} - {selected_product.name}"
            form.product_id.data = str(selected_product.id)
    
    if form.validate_on_submit():
        product = Product.query.get_or_404(form.product_id.data)
        
        if product.quantity < form.quantity.data:
            flash('Quantidade insuficiente em estoque. Sua solicitação será enviada mesmo assim.', 'warning')
        
        # Create pending allocation request
        allocation = Allocation(
            product_id=product.id,
            user_id=current_user.id,
            work_number=form.work_number.data,
            quantity=form.quantity.data,
            notes=form.notes.data,
            status='pending'  # Pending approval
        )
        
        db.session.add(allocation)
        db.session.commit()
        
        flash('Solicitação enviada com sucesso! Aguarde aprovação do almoxarifado.', 'success')
        return redirect(url_for('my_requests'))
    
    return render_template('request_product.html', form=form, selected_product=selected_product)

# Inventory route
@app.route('/inventory')
@login_required
def inventory():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Product.query
    if search:
        query = query.filter(
            Product.name.contains(search) | 
            Product.code.contains(search) |
            Product.supplier_reference.contains(search)
        )
    
    products = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Create form for CSRF token
    form = AllocationForm()
    
    return render_template('inventory.html', products=products, search=search, form=form)

# Allocation history route
@app.route('/allocation_history')
@login_required
def allocation_history():
    page = request.args.get('page', 1, type=int)
    
    if current_user.role == 'almoxarifado':
        allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
    else:
        allocations = Allocation.query.filter_by(user_id=current_user.id).order_by(
            Allocation.allocated_at.desc()
        ).paginate(
            page=page, per_page=20, error_out=False
        )
    
    return render_template('allocation_history.html', allocations=allocations)

# Production user routes
@app.route('/my_requests')
@login_required
def my_requests():
    if current_user.role != 'producao':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    allocations = Allocation.query.filter_by(user_id=current_user.id).order_by(
        Allocation.allocated_at.desc()
    ).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('my_requests.html', allocations=allocations)

# Approval workflow routes for warehouse staff
@app.route('/pending_requests')
@login_required
def pending_requests():
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    pending_allocations = Allocation.query.filter_by(status='pending').order_by(
        Allocation.allocated_at.desc()
    ).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('pending_requests.html', allocations=pending_allocations)

@app.route('/approve_request/<int:allocation_id>', methods=['GET', 'POST'])
@login_required
def approve_request(allocation_id):
    if current_user.role != 'almoxarifado':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    allocation = Allocation.query.get_or_404(allocation_id)
    
    if allocation.status != 'pending':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('pending_requests'))
    
    form = ApprovalForm()
    
    if form.validate_on_submit():
        allocation.status = form.action.data
        allocation.approved_by_id = current_user.id
        allocation.approved_at = brazil_now()
        allocation.approval_notes = form.approval_notes.data
        
        if form.action.data == 'approved':
            # Check if there's enough stock
            if allocation.product.quantity < allocation.quantity:
                flash('Quantidade insuficiente em estoque para aprovação.', 'danger')
                return render_template('approve_request.html', allocation=allocation, form=form)
            
            # Update stock
            log_stock_movement(
                allocation.product, 
                current_user, 
                'allocation', 
                allocation.quantity, 
                f'Solicitação aprovada - Obra {allocation.work_number}'
            )
            
            flash(f'Solicitação aprovada com sucesso!', 'success')
        else:
            flash(f'Solicitação rejeitada.', 'info')
        
        db.session.commit()
        return redirect(url_for('pending_requests'))
    
    return render_template('approve_request.html', allocation=allocation, form=form)

# API routes for autocomplete
@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        Product.name.contains(query) | 
        Product.code.contains(query) |
        Product.supplier_reference.contains(query)
    ).limit(10).all()
    
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'supplier_reference': product.supplier_reference,
            'location': product.location,
            'quantity': product.quantity,
            'unit': product.unit,
            'supplier_name': product.supplier_name,
            'photo_filename': product.photo_filename
        })
    
    return jsonify(result)

# Static file serving
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Create default admin user
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@empresa.com',
            role='almoxarifado',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # No need to create default supplier - using text field
        db.session.commit()
        
        print("Admin user created: admin/admin123")



