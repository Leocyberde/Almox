from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError, EqualTo
from models import User, Product

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Senha', validators=[DataRequired()])

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Confirmar Senha', validators=[
        DataRequired(), EqualTo('password', message='Senhas devem ser iguais')
    ])

class EmployeeForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Função', choices=[
        ('producao', 'Produção'),
        ('almoxarifado', 'Almoxarifado')
    ], validators=[DataRequired()])
    is_admin = BooleanField('Administrador')

class EditEmployeeForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Nova Senha (deixe em branco para manter a atual)', validators=[Length(min=6)])
    role = SelectField('Função', choices=[
        ('producao', 'Produção'),
        ('almoxarifado', 'Almoxarifado')
    ], validators=[DataRequired()])
    is_admin = BooleanField('Administrador')
    is_active = BooleanField('Ativo')

# SupplierForm removed - using text field instead

class ProductForm(FlaskForm):
    code = StringField('Código', validators=[DataRequired(), Length(max=50)])
    name = StringField('Nome do Produto', validators=[DataRequired(), Length(max=200)])
    supplier_reference = StringField('Referência do Fornecedor', validators=[Length(max=100)])
    location = StringField('Local', validators=[DataRequired(), Length(max=100)])
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=0)])
    unit = SelectField('Unidade', choices=[
        ('unidade', 'Unidade'),
        ('metros', 'Metros'),
        ('pacote', 'Pacote'),
        ('cento', 'Cento')
    ], validators=[DataRequired()])
    supplier_name = StringField('Fornecedor', validators=[DataRequired(), Length(max=100)])
    photo = FileField('Foto do Produto', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas arquivos de imagem são permitidos!')
    ])


    def validate_code(self, field):
        # Check if code exists and if it's not the current product being edited
        existing_product = Product.query.filter_by(code=field.data).first()
        if existing_product and (not hasattr(self, 'product_id') or existing_product.id != self.product_id):
            raise ValidationError('Este código já está sendo usado por outro produto.')

class AllocationForm(FlaskForm):
    product_search = StringField('Buscar Produto', validators=[DataRequired()])
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    work_number = StringField('Número da Obra', validators=[DataRequired(), Length(max=50)])
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Observações')

class StockAdjustmentForm(FlaskForm):
    adjustment_type = SelectField('Tipo de Ajuste', choices=[
        ('add', 'Adicionar Estoque'),
        ('remove', 'Remover Estoque')
    ], validators=[DataRequired()])
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Observações', validators=[DataRequired()])

class ProductionRequestForm(FlaskForm):
    product_search = StringField('Buscar Produto', validators=[DataRequired()])
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    work_number = StringField('Número da Obra', validators=[DataRequired(), Length(max=50)])
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Observações/Justificativa')

class ApprovalForm(FlaskForm):
    action = SelectField('Ação', choices=[
        ('approved', 'Aprovar'),
        ('rejected', 'Rejeitar')
    ], validators=[DataRequired()])
    approval_notes = TextAreaField('Observações da Aprovação')