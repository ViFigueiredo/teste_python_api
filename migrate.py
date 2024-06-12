from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from urllib.parse import quote_plus
from dotenv import load_dotenv
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

connection_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=192.168.0.200\\sqlserverfull;"
    "Database=teste_python;"
    "UID=dbAdmin;"
    "PWD=Ctelecom2017;"
    "Encrypt=no"
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
    role = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current)


# Teste de conexão
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
try:
    connection = engine.connect()
    print("Conexão bem-sucedida!")
    connection.close()
except OperationalError:
    print("Falha na conexão. Por favor, verifique suas credenciais e tente novamente.")

# Se a conexão for bem-sucedida, você pode prosseguir com as migrações.
