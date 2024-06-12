from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import pyodbc
import os
import hashlib
import binascii

# Carregar variáveis de ambiente
load_dotenv()

# Carregar o salt
# Certifique-se de codificar o salt para bytes
salt = os.getenv('SALT').encode()

app = Flask(__name__)
# Troque por uma chave secreta real
app.config['JWT_SECRET_KEY'] = 'super-secret'

jwt = JWTManager(app)

# Configuração da conexão
conn = pyodbc.connect(
    'DRIVER={' + os.getenv('DB_DRIVER') + '};'
    'SERVER=' + os.getenv('DB_SERVER') + ';'
    'DATABASE=' + os.getenv('DB_NAME') + ';'
    'UID=' + os.getenv('DB_USER') + ';'
    'PWD=' + os.getenv('DB_PASSWORD') + ';'
    'Encrypt=no'
)

cursor = conn.cursor()


@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    params = request.get_json()
    email = params.get('email', None)
    password = params.get('password', None)

    if not email:
        return jsonify({"msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    cursor.execute(f"SELECT * FROM [user] WHERE email = '{email}'")
    user = cursor.fetchone()

    # Gera o hash da senha fornecida usando scrypt
    password_hash = hashlib.scrypt(
        password.encode(), salt=salt, n=16384, r=8, p=1, maxmem=0, dklen=64)
    # Converte para hexadecimal e trunca para 128 caracteres
    password_hash = binascii.hexlify(password_hash).decode()[:128]

    print(user.password)
    print(password_hash)

    # Compara o hash truncado com o hash armazenado
    if user is None or user.password != password_hash:
        return jsonify({"msg": "Bad email or password"}), 401

    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token), 200


@app.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.get_json()
    new_name = data.get('name')
    new_email = data.get('email')
    new_password = data.get('password')

    if new_password:
        # Gera o hash da nova senha fornecida usando scrypt e trunca para 128 caracteres
        new_password_hash = hashlib.scrypt(new_password.encode(
        ), salt=salt, n=16384, r=8, p=1, maxmem=0, dklen=64)
        new_password_hash = binascii.hexlify(new_password_hash).decode()[:128]
        cursor.execute(
            f"UPDATE [user] SET password = '{
                new_password_hash}' WHERE id = {user_id}"
        )

    if new_name:
        cursor.execute(
            f"UPDATE [user] SET name = '{new_name}' WHERE id = {user_id}"
        )

    if new_email:
        cursor.execute(
            f"UPDATE [user] SET email = '{new_email}' WHERE id = {user_id}"
        )

    conn.commit()

    return jsonify({'message': 'User updated successfully'}), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    cursor.execute(f"DELETE FROM [user] WHERE id = {user_id}")
    conn.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


@app.route('/users', methods=['POST'])
@jwt_required()
def add_user():
    data = request.get_json()
    # Gera o hash da senha fornecida usando scrypt e trunca para 128 caracteres
    password_hash = hashlib.scrypt(data['password'].encode(
    ), salt=salt, n=16384, r=8, p=1, maxmem=0, dklen=64)
    password_hash = binascii.hexlify(password_hash).decode()[:128]
    # Se 'role' não estiver presente, usa 0 como padrão
    role = data.get('role', 0)
    cursor.execute(
        f"INSERT INTO [user] (name, email, password, role) VALUES ('{data['name']}', '{
            data['email']}', '{password_hash}', '{role}')"
    )
    conn.commit()

    return jsonify({'message': 'User added successfully'}), 201


@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    cursor.execute(f"SELECT * FROM [user] WHERE id = {user_id}")

    row = cursor.fetchone()
    if row is None:
        return jsonify({'error': 'User not found'}), 404

    user = {
        'id': row.id,
        'name': row.name,
        'email': row.email,
        'password': row.password,
        'role': row.role,
    }
    return jsonify(user)


@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    cursor.execute("SELECT * FROM [user]")

    users = []
    for row in cursor:
        users.append({
            'id': row.id,
            'name': row.name,
            'email': row.email,
            'password': row.password,
            'role': row.role,
        })

    return jsonify(users)


@app.route('/', methods=['GET'])
@jwt_required()
def home():
    msg = 'Página inicial da API de usuários em python.'
    return jsonify({"msg": msg})


if __name__ == '__main__':
    app.run(debug=True)
