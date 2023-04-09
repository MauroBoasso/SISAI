from wtforms import Form, StringField, PasswordField, IntegerField, TextAreaField, validators, SelectField, FileField
from flask_login import UserMixin, LoginManager

class RegisterForm(Form, UserMixin):
    username = StringField('Nombre de Usuario', [validators.Length(max=200)])
    email = StringField('Email', [validators.Length(max=200)])
    dni = StringField('DNI', [validators.Length(min=8, max=8)])
    password = PasswordField('Contraseña', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Las contraseñas no coinciden')
    ])
    confirm = PasswordField('Confirmar Contraseña')
    depto_piso = SelectField('Numero de Piso', choices=[(1, 1), (2, 2), (3, 3), (4, 4)])
    depto_no = SelectField('Numero de Departamento', choices=[(1, 1), (2, 2), (3, 3), (4, 4)])
    role = StringField()
    # foto = FileField('Foto')

class ClaimForm(Form):
    category = SelectField('Categoria', choices=[('Pintura', 'Pintura'), ('Albañileria', 'Albañileria'), ('Limpieza', 'Limpieza'), ('Convivencia', 'Convivencia')])
    body = TextAreaField('Cuerpo', [validators.Length(min=10)])
    state = StringField()