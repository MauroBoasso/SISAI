import os
from flask_mysqldb import MySQL
from os.path import join, dirname, realpath

from flask import Flask, flash, render_template, request, redirect, url_for, session, logging, send_from_directory, Response
from flask_login import fresh_login_required
from functools import wraps

from passlib.hash import md5_crypt as md5
from passlib.hash import sha256_crypt as sha256
from passlib.hash import sha512_crypt as sha512

import socketio
from flask_socketio import SocketIO, send

from config import config
from models import RegisterForm, ClaimForm
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/uploads/')
app = Flask(__name__)
db = MySQL(app)
socketio = SocketIO(app)
app.config['UPLOAD_FOLDER'] = UPLOADS_PATH
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

@app.route("/static/uploads/<nombreFoto>")
def uploads(nombreFoto):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nombreFoto)

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    if 'logged_in' in session:
        username = session['username']

        cur = db.connection.cursor()

        result = cur.execute("SELECT * FROM usuarios WHERE username = %s", [username])

        users = cur.fetchone()

        db.connection.commit()

        cur.close()
        return render_template("home.html", username=username)
    else:
        return render_template("about.html")
    
@app.route('/chat')
def chat():
    nombre = session['username']

    return render_template("chat.html",  nombre=nombre)

@socketio.on('message')
def handleMessage(msg):
    print('Mensaje: ' + msg)
    send(msg, broadcast = True)

@app.route('/register', methods = ["GET","POST"])
def register():

    form = RegisterForm(request.form)
   
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256.encrypt(str(form.password.data))
        dni = form.dni.data
        role = 'user'
        now = datetime.now()
        tiempo = now.strftime("%Y%H%M")

        cur = db.connection.cursor()

        query = cur.execute("SELECT dni FROM usuarios WHERE dni = %s", [dni])

        db.connection.commit()

        cur.close()
       
        if query == 1:
            flash('Usuario ya registrado...', 'danger')
            return redirect(request.url)

        if 'foto' not in request.files:
            flash('Archivo no seleccionado', 'warning')
            return redirect(request.url)

        foto = request.files['foto']
        if foto.filename == '':
            flash('Debes subir una Foto', 'warning')
            return render_template("register.html", form=form)

        if foto and allowed_file(foto.filename):
            nuevoNombreFoto = tiempo + foto.filename
            filename = secure_filename(nuevoNombreFoto)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            cur = db.connection.cursor()

            cur.execute("INSERT INTO usuarios(username, email, dni, role, foto, password) VALUES(%s, %s, %s, %s, %s, %s)", (username, email, dni, role, nuevoNombreFoto, password))

            db.connection.commit()

            cur.close()

            flash('Usuario registrado, Solo falta Iniciar Sesión', 'success')

            return redirect(url_for('login'))
        else:
            flash('Solo se permiten extensiones jpg, jpeg y png', 'warning')
            return render_template("register.html", form=form)

    return render_template("register.html", form=form)

@app.route('/login', methods = ["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        dni = request.form['dni']
        password_candidate = request.form['password']

        cur = db.connection.cursor()

        result = cur.execute("SELECT password FROM usuarios WHERE dni = %s AND username = %s", [dni, username])

        if result > 0:
            data = cur.fetchone()
            password = data[0]

            if sha256.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('Bienvenido ' + session['username'] + ' has Inciado Sesion correctamente', 'success')
                return redirect(url_for('home'))
            else:
                flash('Inicio de sesion Invalido', 'danger')
                error = 'Inicio de sesion Invalido'
                return render_template('login.html', error=error)

            cur.close()
        else:
            flash('Usuario no encontrado', 'warning')
            error = 'Usuario no encontrado'
            return render_template('login.html', error=error)

    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Primero debes Inciar Sesión', 'info')
            return redirect(url_for('login'))
    return wrap

def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        cur = db.connection.cursor()

        query = cur.execute("SELECT dni FROM usuarios")

        query = cur.fetchall()

        for dni in query:
            print(dni)

        if query[0] == 'admin':
            return f(*args, **kwargs)
        else:
            flash('Debes ser administrador', 'info')
            return redirect(url_for('home'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Estas Desconectado, Por Favor Inicia Sesion para disfrutar de nuestro excelente servicio', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    return render_template("profile.html")

@app.route('/usuarios')
@is_logged_in
@is_admin
def usuarios():
    cur = db.connection.cursor()

    result = cur.execute("SELECT * FROM usuarios")

    users = cur.fetchall()

    if result > 0:
        return render_template("usuarios.html", users=users)
    else:
        flash('No se encontraton Usuarios', 'info')
        msg = 'No se encontraton Usuarios'
        return render_template("dashboard.html", msg=msg)
    cur.close()

@app.route('/edit_usuario/<string:dni>', methods=['GET', 'POST'])
@is_logged_in
# @is_admin
def edit_usuario(dni):
    cur = db.connection.cursor()

    result = cur.execute("SELECT * FROM usuarios WHERE dni = %s", [dni])

    users = cur.fetchall()
    print(users)

    db.connection.commit()

    cur.close()

    return render_template('edit_usuario.html', users=users)

@app.route('/update', methods=['GET', 'POST'])
@is_logged_in
# @is_admin
def update():

    username = request.form["username"]
    email = request.form["email"]
    role = request.form["role"]
    dni = request.form["dni"]
    foto = request.files['foto']

    cur = db.connection.cursor()

    now=datetime.now()
    tiempo = now.strftime("%Y%H%M")

    if foto.filename != '':
        nuevoNombreFoto = tiempo + foto.filename
        filename = secure_filename(nuevoNombreFoto)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur.execute("SELECT foto FROM usuarios WHERE dni=%s", [dni])

        fila=cur.fetchall()

        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], fila[0][0]))

        cur.execute("UPDATE usuarios SET foto=%s WHERE dni = %s", (nuevoNombreFoto, dni))

        db.connection.commit()

    cur.execute("UPDATE usuarios SET username=%s, email=%s, role=%s WHERE dni = %s", (username, email, role, dni))

    db.connection.commit()

    cur.close()

    flash('Usuario editado Correctamente', 'success')

    return redirect('usuarios')

@app.route('/delete_user/<string:dni>', methods=['GET', 'POST'])
@is_logged_in
# @is_admin
def delete_user(dni):
    cur = db.connection.cursor()

    role = cur.execute("SELECT role FROM usuarios")

    role = cur.fetchall()
    print(role)

    if role == 'admin':
        flash('El usuario es administrador', 'warning')
        return redirect(url_for('usuarios'))  
    else:
        cur = db.connection.cursor()

        cur.execute("DELETE FROM usuarios WHERE dni = %s", [dni])

        db.connection.commit()

        cur.close()

        flash('Usuario Eliminado', 'success')

        return redirect(url_for('usuarios'))

@app.route('/dashboard')
@is_logged_in
# @is_admin
def dashboard():
    cur = db.connection.cursor()

    result = cur.execute("SELECT * FROM claims")
    # result = cur.execute("SELECT * FROM claims WHERE author = %s", [session['username']])

    claims = cur.fetchall()

    if result > 0:
        return render_template("dashboard.html", claims=claims)
    else:
        flash('No se encontraton Reclamos', 'info')
        msg = 'No se encontraton Reclamos'
        return render_template("dashboard.html", msg=msg)
    cur.close()

@app.route('/add_claim', methods=['GET', 'POST'])
@is_logged_in
def add_claim():
    form = ClaimForm(request.form)
    if request.method == 'POST' and form.validate():
        category = form.category.data
        body = form.body.data
        author = session['username']
        state = 'Pendiente'
        date = datetime.now()

        cur = db.connection.cursor()

        cur.execute("INSERT INTO claims(category, body, author, date, state) VALUES(%s, %s, %s, %s, %s)", (category, body, author, date, state))

        db.connection.commit()

        cur.close()

        flash('Reclamo Creado', 'success')

        return redirect(url_for('miclaims'))

    return render_template('add_claim.html', form=form)

@app.route('/miclaims')
@is_logged_in
def miclaims():
    cur = db.connection.cursor()

    result = cur.execute("SELECT * FROM claims WHERE author = %s",  [session['username']])

    claims = cur.fetchall()

    if result > 0:
        return render_template("miclaims.html", claims=claims)
    else:
        flash('No se encontraton Reclamos', 'info')
        msg = 'No se encontraton Reclamos'
        return render_template("miclaims.html", msg=msg)
    cur.close()

@app.route('/claim/<string:id>/')
@is_logged_in
def claim(id):
    cur = db.connection.cursor()

    result = cur.execute("SELECT * FROM claims WHERE id = %s", [id])
    claim = cur.fetchone()

    return render_template("claim.html", claim=claim)

@app.route('/edit_claim/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_claim(id):
    cur = db.connection.cursor()

    result = cur.execute("SELECT * FROM claims WHERE id = %s", [id])

    claims = cur.fetchone()

    form = ClaimForm(request.form)

    form.category.data = claims[1]
    form.body.data = claims[2]

    if request.method == 'POST' and form.validate():
        category = request.form['category']
        body = request.form['body']

        cur = db.connection.cursor()

        cur.execute("UPDATE claims SET category=%s, body=%s WHERE id = %s", (category, body, id))

        db.connection.commit()

        cur.close()

        flash('Reclamo Editado', 'success')

        return redirect(url_for('miclaims'))
        # return redirect(url_for('dashboard'))

    return render_template('edit_claim.html', form=form)

@app.route('/delete_claim/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_claim(id):
    cur = db.connection.cursor()

    cur.execute("DELETE FROM claims WHERE id = %s", [id])

    db.connection.commit()

    cur.close()

    flash('Reclamo Eliminado', 'success')

    return redirect(url_for('dashboard'))
    
if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run()
    socketio.run(app)