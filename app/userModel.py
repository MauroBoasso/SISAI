from app import db

class User(db.Model):
    __tablename__ = 'user' 
    id= db.Column(db.Integer, primary_key=True, autoincrement = True)
    username = db.Column(db.String(250))
    dni = db.Column(db.Integer, unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    depto_piso = db.Column(db.String(255))
    depto_no = db.Column(db.String(255))
    role = db.Column(db.String(12))
    path_foto= db.Column(db.String(255))

    def __repr__(self):
        return f'<User {self.username}>'
from datetime import datetime

class Claim(db.Model):
    __tablename__ = 'claims' 
    id= db.Column(db.Integer, primary_key=True, autoincrement = True)
    category = db.Column(db.String(250))
    body = db.Column(db.Text)
    name_author = db.Column(db.String(50))
    id_author = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True),default=datetime.utcnow)
    state = db.Column(db.String(255))
    depto_no = db.Column(db.String(12))
    foto= db.Column(db.String(255))

    def __repr__(self):
        return f'<idclaim {self.id}>'