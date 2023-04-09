import os

from flask_migrate import Migrate
from flask_mysqldb import MySQL
from os.path import join, dirname, realpath

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash, render_template, request, redirect, url_for, session, logging, send_from_directory, Response
from flask_login import fresh_login_required
from flask_principal import Principal
from functools import wraps

from passlib.hash import md5_crypt as md5
from passlib.hash import sha256_crypt as sha256
from passlib.hash import sha512_crypt as sha512

from app.config import DevelopmentConfig
from app.models import RegisterForm, ClaimForm
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/uploads/')
UPLOADS_PATH_CLAIMS = join(dirname(realpath(__file__)), 'static/claims/')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/SISAIdb'
principals = Principal(app)
db = SQLAlchemy(app)
# db.init_app(app)
migrate = Migrate(app, db)

from app.userModel import User
from app.userModel import Claim

# app.config['UPLOAD_FOLDER'] = UPLOADS_PATH_CLAIMS
# app.config['UPLOAD_FOLDER'] = UPLOADS_PATH
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# Retorna el directorio de las imagenes de perfil
@app.route("/static/uploads/<nombrePerfilFoto>")
def uploads(nombrePerfilFoto):
    return send_from_directory(join(dirname(realpath(__file__)), 'static/uploads/'), nombrePerfilFoto)

# Retorna el directorio de las imagenes de reclamos
@app.route("/static/claims/<nombreReclamoFoto>")
def claims(nombreReclamoFoto):
    return send_from_directory(join(dirname(realpath(__file__)), 'static/claims/'), nombreReclamoFoto)

# Retorna el tipo de extension que son validas
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Directorio de inicio
@app.route('/')
def home():
    # retorna el template segun di esta iniciada la sesion
    if 'logged_in' in session:
        print(str(session))
        return render_template("home.html", username=session['username'])
    else:
        return render_template("about.html")

# Vista de registro
@app.route('/register', methods = ["GET","POST"])
def register():
    # Inicia variable for con la clase
    form = RegisterForm(request.form)
   
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        # encripta contraseña
        password = sha256.encrypt(str(form.password.data))
        dni = form.dni.data
        depto_piso = form.depto_piso.data
        depto_no = form.depto_no.data
        role = 'user'
        # incia variable de fecha y le da formato
        now = datetime.now()
        tiempo = now.strftime("%Y%H%M")

        # Verificar si el número de DNI ya existe
        dni_existente = User.query.filter_by(dni=dni).first()

        if dni_existente:
            flash("El número de DNI ya está registrado.")
            return redirect(request.url)
       
        # Comprueba foto en input
        if 'foto' not in request.files:
            flash('Archivo no seleccionado', 'warning')
            return redirect(request.url)
        
        # Inicia variable foto con el archivo del registro
        foto = request.files['foto']
        # Comprueba si exite nombre en el input
        if foto.filename == '':
            flash('Debes subir una Foto', 'warning')
            return render_template("register.html", form=form)
        # comprueba si exite la variable foto y la extension el valida
        if foto and allowed_file(foto.filename):
            nuevoNombreFoto = foto.filename
            filename = secure_filename(nuevoNombreFoto)
            # guarda imagen en la carpeta uploads en static
            foto.save(os.path.join(join(dirname(realpath(__file__)), 'static/uploads/'), filename))
            # Inserta en la tabla users los datos del registro
            nuevo_usuario = User(username=username, dni=dni, email=email, password=password, depto_piso=depto_piso, depto_no = depto_no, role=role,path_foto=filename)
            from sqlalchemy.exc import IntegrityError
            
            try:
                db.session.add(nuevo_usuario)
                db.session.commit()
                # Envia mensaje si el registro fue valido
                flash('Usuario registrado, Solo falta Iniciar Sesión', 'success')
                return redirect(url_for('login'))
            except IntegrityError as e:
                print (e)
                db.session.rollback()
                flash('Los datos ingresados coinciden con otros ya ingresados', 'warning')
                return render_template("register.html", form=form)
    
        else:
            # Envia mensaje si las extensiones no son validas
            flash('Solo se permiten extensiones jpg, jpeg y png', 'warning')
            return render_template("register.html", form=form)

    return render_template("register.html", form=form)

# Vista de logueo
@app.route('/login', methods = ["GET","POST"])
def login():
    if request.method == 'POST':
        # Inicia variables segun el formulario login
        username = request.form['username']
        dni = request.form['dni']
        # variable de candidato a la contraseña
        password_candidate = request.form['password']

        user = User.query.filter_by(dni=dni, username=username).first()
        # Comprueba si exite contraseña
        if user is not None:
            password = user.password
            # verifica si el candidato a contraseña es igual a la contraseña en la bd
            if sha256.verify(password_candidate, password):

                # inicia varibales de sesion
                session['logged_in'] = True
                session['username'] = user.username
                session['dni'] = user.dni
                session['role'] = user.role
                session['foto'] = str(user.path_foto)
                session['depto_piso'] = user.depto_piso
                session['depto_no'] = user.depto_no

                # Mensaje de bienvenida
                flash('Bienvenido ' + session['username'] + ' has Inciado Sesion correctamente', 'success')
                return redirect(url_for('home'))
            else:
                # Mensaje de sesion invalido
                flash('Inicio de sesion Invalido', 'danger')
                error = 'Inicio de sesion Invalido'
                return render_template('login.html', error=error)

        else:
            # mensaje si el usuario no existe
            flash('Usuario no encontrado', 'warning')
            error = 'Usuario no encontrado'
            return render_template('login.html', error=error)

    return render_template('login.html')

# decorador para restringuir templates segun si esta inicada la sesion
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Primero debes iniciar Sesión', 'info')
            return redirect(url_for('login'))
    return wrap

# decorador para restringuir templates el rol del usuario
def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['role'] == 'admin':
            return f(*args, **kwargs)
        elif 'logged_in' in session:
            flash('Debes ser Administrador', 'warning')
            return redirect(url_for('home'))
        else:
            flash('Debes ser Administrador o Inicia Sesion', 'warning')
            return redirect(url_for('login'))
    return wrap

# Cierre de Sesion
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    # Mensaje de desconeccion
    flash('Estas Desconectado, Por Favor Inicia Sesion para disfrutar de nuestro excelente servicio', 'info')
    return redirect(url_for('home'))

# Vista de perfil
@app.route('/profile')
@is_logged_in
def profile():

    user = User.query.filter_by(dni=session["dni"]).first()

    # Comprueba si existen ususarios
    return render_template("profile.html", user=user)

# Vista Crud de usuarios
@app.route('/usuarios')
@is_admin
@is_logged_in
def usuarios():
    # selecciona todos lod datos de los usuarios
    users = User.query.all()
    # Comprueba si existen ususarios
    if len(users) > 0:
        return render_template("usuarios.html", users=users)
    else:
        # Mensaje si no exiten usuarios
        flash('No se encontraton Usuarios', 'info')
        msg = 'No se encontraton Usuarios'
        return render_template("dashboard.html", msg=msg)

# Vista Para editar usuarios
@app.route('/edit_usuario/<string:dni>', methods=['GET', 'POST'])
@is_logged_in
def edit_usuario(dni):
    user= User.query.filter_by(dni=dni).first()
    return render_template('edit_usuario.html', user=user)

# Actualiza usuarios
@app.route('/update', methods=['GET', 'POST'])
@is_logged_in
@is_admin
def update():
    # inicia variables de usuarios
    username = request.form["username"]
    email = request.form["email"]
    role = request.form["role"]
    dni = request.form["dni"]
    foto = request.files['foto']
    
      # inicia variable tiempo
    now=datetime.now()
    tiempo = now.strftime("%Y%H%M") 
    user=User.query.filter_by(dni=dni).first()
    
    # Comprueba que hay un archivo en el imput de img
    if foto.filename != '':
        nuevoNombreFoto = foto.filename
        filename = secure_filename(nuevoNombreFoto)
        
        # elimina foto del directorio
        os.remove(os.path.join(join(dirname(realpath(__file__)), 'static/uploads/'), user.path_foto))
        
        # guarda img en el directorio
        foto.save(os.path.join(join(dirname(realpath(__file__)), 'static/uploads/'), filename))
  
    else:
        filename=user.path_foto
        
    # ejecuta query de actualizacion de la foto
    # actualizar el campo foto
    user.path_foto = filename
    
    # actualizar la sesión del usuario con la nueva ruta de la imagen
    session['foto'] = filename
    
    # guardar la sesión actualizada
    session.modified = True

    # guardar los cambios en la base de datos
    db.session.commit()

    user.username=username
    user.email=email
    user.role=role
    user.dni=dni
    db.session.commit()
    # Mensaje de actualizacion
    flash('Usuario editado Correctamente', 'success')

    return redirect('usuarios')

# Elimina usuarios
@app.route('/delete_user/<string:dni>', methods=['GET', 'POST'])
@is_logged_in
def delete_user(dni):
    # Selecciona rol de los usuarios segun el dni seleccionado
    role = (User.query.filter_by(dni=dni).first()).role 
    # print(role)

# Comprueba el rol 'admin'
    if role == 'admin':
        # Si el usuarios es admin no lo elimina
        flash('El usuario es administrador', 'warning')
        return redirect(url_for('usuarios'))  
    else:
        # Ejecuta query para eliminar usuario segun dni seleccionado
        User.query.filter_by(dni=dni).delete()
        db.session.commit()
        # mensaje de eliminacion
        flash('Usuario Eliminado', 'success')
        if session['role'] != 'admin':    
            session.clear()
            return redirect(url_for('home'))
        else: 
            return redirect(url_for('usuarios'))
# Vista re reclamos
@app.route('/dashboard')
@is_logged_in
@is_admin
def dashboard():
    # selecciona todos los datos de los reclamos
    claims=Claim.query.all()

    # comprueba si exiten reclamos
    if len(claims) > 0:
        return render_template("dashboard.html", claims=claims)
    else:
        # mensaje si no existen reclamos
        flash('No se encontraton Reclamos', 'info')
        msg = 'No se encontraton Reclamos'
        return render_template("dashboard.html", msg=msg)
    

# Crea reclamo
@app.route('/add_claim', methods=['GET', 'POST'])
@is_logged_in
def add_claim():
    # inicia form en la clase reclamos
    form = ClaimForm(request.form)

    # comprueba el metodo del form y la si esta validado
    if request.method == 'POST' and form.validate():
        # Inicia variables con datos del form
        category = form.category.data
        body = form.body.data
        name_author = session['username']
        id_author = session['dni']
        state = 'Pendiente'
        now = datetime.now()
        depto_no = session['depto_no']
        tiempo = now.strftime("%Y%H%M")

        if 'foto' not in request.files:
            flash('Archivo no seleccionado', 'warning')
            return redirect(request.url)

        foto = request.files['foto']
        if foto.filename == '':
            flash('Debes subir una Foto', 'warning')
            return render_template("add_claim.html", form=form)

        if foto and allowed_file(foto.filename):
            nuevoNombreFotoReclamo = foto.filename
            filename = secure_filename(nuevoNombreFotoReclamo)
            foto.save(os.path.join(join(dirname(realpath(__file__)), 'static/claims/'), filename))

            claim=Claim(category=category, body=body, name_author=name_author, id_author=id_author, date=now, state=state, depto_no=depto_no, foto=nuevoNombreFotoReclamo)
            db.session.add(claim)
            db.session.commit()
            flash('Reclamo Creado', 'success')

            return redirect(url_for('miclaims'))
        else:
            flash('Solo se permiten extensiones jpg, jpeg y png', 'warning')
            
            return render_template("add_claim.html", form=form)

    return render_template('add_claim.html', form=form)

# Vista de mis reclamos
@app.route('/miclaims')
@is_logged_in
def miclaims():
    # selecciona los datos de reclamo del usuario
    claims=Claim.query.filter_by(id_author=session["dni"]).all()

    # comprueba si existen reclamos del usuario
    if len(claims) > 0:

        return render_template("miclaims.html", claims=claims)
    else:
        # Mensjae si no se econtraton reclamos del usuario
        flash('No se encontraton Reclamos', 'info')
        msg = 'No se encontraton Reclamos'

        return render_template("miclaims.html", msg=msg)
  

# Vista de reclamo de forma individual
@app.route('/claim/<int:id>/')
@is_logged_in
def claim(id):
    # Selecciona todos los reclamos del usuario 

    claim=Claim.query.filter_by(id=id).first()

    return render_template("claim.html", claim=claim)


@app.route('/edit_claim/<int:id>', methods=['GET','POST'])
@is_logged_in
def edit_claim(id):
    result=Claim.query.filter_by(id=id).first()

    formdb= ClaimForm(category=result.category, body=result.body, state=result.state)
    form = ClaimForm(request.form)
    if request.method == 'POST' and form.validate():
        category=form.category.data 
        body= form.body.data
        result.category=category
        result.body=body
        db.session.commit()

        flash('Reclamo Editado', 'success')

        return redirect(url_for('miclaims'))
        # return redirect(url_for('dashboard'))

    else: 
        print (result.category)
        print(result.body)
        return render_template('edit_claim.html', claim=formdb,claim_id=result.id)

@app.route('/delete_claim/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_claim(id):
    Claim.query.filter_by(id=id).delete()
    db.session.commit()
    flash('Reclamo Eliminado', 'success')

    return redirect(url_for('miclaims'))
    
