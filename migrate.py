from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine, ForeignKey, text
from sqlalchemy.exc import OperationalError
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

connection_str = (
    f"Driver={os.getenv('DB_DRIVER')};"
    f"Server={os.getenv('DB_SERVER')};"
    f"Database={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=no"
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mssql+pyodbc:///?odbc_connect={
    quote_plus(connection_str)}'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    role_id = db.Column(db.Integer, ForeignKey('role.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    value = db.Column(db.String(5))
    users = db.relationship('User', backref='role', lazy=True)
    created_at = db.Column(db.DateTime, server_default=text("(getdate())"))
    updated_at = db.Column(db.DateTime, server_default=text(
        "(getdate())"), onupdate=text("(getdate())"))


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(128), unique=True)


class RoleRoute(db.Model):
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey(
        'route.id'), primary_key=True)
    role = db.relationship('Role', backref=db.backref(
        'role_routes', cascade='all, delete-orphan'))
    route = db.relationship('Route', backref=db.backref(
        'role_routes', cascade='all, delete-orphan'))


# Teste de conexão
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
try:
    connection = engine.connect()
    print("Conexão bem-sucedida!")
    connection.close()
except OperationalError:
    print("Falha na conexão. Por favor, verifique suas credenciais e tente novamente.")
