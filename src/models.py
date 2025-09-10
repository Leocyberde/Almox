from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Configurar timezone do Brasil (UTC-3)
# BRAZIL_TZ = timezone(timedelta(hours=-3)) # This line is replaced by the new function logic

def brazil_now():
    """Get current time in Brazil timezone"""
    from datetime import datetime
    import pytz
    utc = pytz.timezone('UTC')
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    utc_time = datetime.now(utc)
    return utc_time.astimezone(brazil_tz).replace(tzinfo=None)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='producao')  # 'almoxarifado', 'producao'
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=brazil_now)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reset_token = db.Column(db.String(120), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    # Relationships
    allocations = db.relationship('Allocation', foreign_keys='Allocation.user_id', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Supplier model removed - using text field instead

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    supplier_reference = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0) # This line is not changed by the provided changes
    unit = db.Column(db.String(20), nullable=False)  # 'unidade', 'metros', 'pacote', 'cento'
    photo_filename = db.Column(db.String(255), nullable=True)
    supplier_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=brazil_now)
    updated_at = db.Column(db.DateTime, default=brazil_now, onupdate=brazil_now)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    allocations = db.relationship('Allocation', backref='product', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.code} - {self.name}>'

class Allocation(db.Model):
    __tablename__ = 'allocations'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_number = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    allocated_at = db.Column(db.DateTime, default=brazil_now)
    notes = db.Column(db.Text, nullable=True)

    # Approval workflow fields
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)

    # Relationships
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_allocations')

    def __repr__(self):
        return f'<Allocation {self.product.code} -> Obra {self.work_number} ({self.status})>'

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # 'add', 'remove', 'allocation'
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=brazil_now)

    # Foreign key to user
    user = db.relationship('User', backref='stock_movements')

    def __repr__(self):
        return f'<StockMovement {self.product.code} {self.movement_type} {self.quantity}>'