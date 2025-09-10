import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import secrets
from datetime import datetime, timedelta
from flask_mail import Message
from app import mail

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file to the uploads directory"""
    if file and file.filename:
        try:
            # Check if file type is allowed
            if not allowed_file(file.filename):
                print(f"Tipo de arquivo não permitido: {file.filename}")
                return None

            # Generate unique filename
            filename = secure_filename(file.filename)
            if not filename:
                return None

            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            # Ensure upload directory exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Save file
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            # Verify file was saved
            if os.path.exists(filepath):
                return unique_filename
            else:
                return None

        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return None
    return None

def delete_uploaded_file(filename):
    """Delete uploaded file"""
    if filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)

def generate_reset_token():
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

def send_reset_email(user, token):
    """Send password reset email"""
    try:
        msg = Message(
            'Redefinição de Senha - Sistema de Estoque',
            recipients=[user.email]
        )

        reset_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/reset_password?token={token}"

        msg.body = f'''
Olá {user.username},

Você solicitou a redefinição de sua senha no Sistema de Controle de Estoque.

Para redefinir sua senha, clique no link abaixo:
{reset_url}

Este link expirará em 1 hora.

Se você não solicitou esta redefinição, ignore este email.

Atenciosamente,
Equipe do Sistema de Estoque
        '''

        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar email de redefinição: {e}")
        return False

def format_quantity(quantity, unit):
    """Format quantity with unit for display"""
    quantity_str = str(int(quantity))  # Convert to integer string
    unit_display = {
        'unidade': 'un',
        'metros': 'm',
        'pacote': 'pct',
        'cento': 'cto'
    }
    return f"{quantity_str} {unit_display.get(unit, unit)}"

def log_stock_movement(product, user, movement_type, quantity, notes=""):
    """Log stock movement for audit trail"""
    from models import StockMovement
    from app import db

    previous_quantity = product.quantity

    if movement_type == 'add':
        new_quantity = previous_quantity + quantity
    elif movement_type == 'remove':
        new_quantity = max(0, previous_quantity - quantity)
    elif movement_type == 'allocation':
        new_quantity = max(0, previous_quantity - quantity)
    else:
        new_quantity = previous_quantity

    movement = StockMovement(
        product_id=product.id,
        user_id=user.id,
        movement_type=movement_type,
        quantity=quantity,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        notes=notes
    )

    db.session.add(movement)
    product.quantity = new_quantity

    return movement