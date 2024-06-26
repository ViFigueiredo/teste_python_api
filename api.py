from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from functools import wraps
import pyodbc
import os
import hashlib
import binascii


load_dotenv()  # Carregar variáveis de ambiente
salt = os.getenv('SALT').encode()  # Carregar/codificar para bytes o salt
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


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()
            cursor.execute(
                f"SELECT * FROM [user] WHERE email = '{current_user}'")
            user = cursor.fetchone()
            if user.role not in roles:
                return jsonify({"msg": "Permission denied"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/role_routes', methods=['POST'])
# @jwt_required()
def add_role_route():
    data = request.get_json()
    cursor.execute(
        f"INSERT INTO [role_routes] (role_id, route_id) VALUES ('{
            data['role_id']}', '{data['route_id']}')"
    )
    conn.commit()
    return jsonify({'message': 'Role route added successfully'}), 201


@app.route('/role_routes/<int:role_id>/<int:route_id>', methods=['DELETE'])
# @jwt_required()
def delete_role_route(role_id, route_id):
    cursor.execute(f"DELETE FROM [role_routes] WHERE role_id = {
                   role_id} AND route_id = {route_id}")
    conn.commit()
    return jsonify({'message': 'Role route deleted successfully'}), 200


@app.route('/role_routes/<int:role_id>/<int:route_id>', methods=['PUT'])
# @jwt_required()
def update_role_route(role_id, route_id):
    data = request.get_json()
    new_role_id = data.get('role_id')
    new_route_id = data.get('route_id')

    if new_role_id:
        cursor.execute(f"UPDATE [role_routes] SET role_id = '{
                       new_role_id}' WHERE role_id = {role_id} AND route_id = {route_id}")

    if new_route_id:
        cursor.execute(f"UPDATE [role_routes] SET route_id = '{
                       new_route_id}' WHERE role_id = {role_id} AND route_id = {route_id}")

    conn.commit()
    return jsonify({'message': 'Role route updated successfully'}), 200


@app.route('/role_routes/<int:role_id>/<int:route_id>', methods=['GET'])
# @jwt_required()
def get_role_route(role_id, route_id):
    cursor.execute(
        f"SELECT * FROM [role_routes] WHERE role_id = {role_id} AND route_id = {route_id}")

    row = cursor.fetchone()
    if row is None:
        return jsonify({'error': 'Role route not found'}), 404

    role_route = {
        'role_id': row.role_id,
        'route_id': row.route_id,
    }
    return jsonify(role_route)


@app.route('/role_routes', methods=['GET'])
# @jwt_required()
def get_role_routes():
    cursor.execute("SELECT * FROM [role_routes]")

    role_routes = []
    for row in cursor:
        role_routes.append({
            'role_id': row.role_id,
            'route_id': row.route_id,
        })

    return jsonify(role_routes)


@app.route('/roles/<int:role_id>', methods=['PUT'])
# @jwt_required()
# @role_required([0,1,2,3...])
def update_role(role_id):
    data = request.get_json()
    new_name = data.get('name')
    new_value = data.get('value')

    if new_name:
        cursor.execute(f"UPDATE [role] SET name = '{
                       new_name}' WHERE id = {role_id}"
                       )

    if new_value:
        cursor.execute(
            f"UPDATE [role] SET value = '{new_value}' WHERE id = {role_id}"
        )
    conn.commit()

    return jsonify({'message': 'role updated successfully'}), 200


@app.route('/roles/<int:role_id>', methods=['DELETE'])
# @jwt_required()
# @role_required([0,1,2,3...])
def delete_role(role_id):
    cursor.execute(f"DELETE FROM [role] WHERE id = {role_id}")
    conn.commit()

    return jsonify({'message': 'role deleted successfully'}), 200


@app.route('/roles', methods=['POST'])
# @jwt_required()
# @role_required([0,1,2,3...])
def add_role():
    data = request.get_json()
    try:
        cursor.execute(
            f"INSERT INTO [role] (name, value) VALUES ('{
                data['name']}', '{data['value']}')"
        )
        conn.commit()
        return jsonify({'message': 'role added successfully'}), 201
    except pyodbc.IntegrityError:
        conn.rollback()  # Adicionado rollback aqui
        return jsonify({'message': 'role already exists'}), 400


@app.route('/roles/<int:role_id>', methods=['GET'])
# @jwt_required()
# @role_required([0,1,2,3...])
def get_role(role_id):
    cursor.execute(f"SELECT * FROM [role] WHERE id = {role_id}")

    row = cursor.fetchone()
    if row is None:
        return jsonify({'error': 'role not found'}), 404

    role = {
        'id': row.id,
        'name': row.name,
        'value': row.value,
    }
    return jsonify(role)


@app.route('/roles', methods=['GET'])
# @jwt_required()
# @role_required([0,1,2,3])
def get_roles():
    cursor.execute("SELECT * FROM [role]")

    roles = []
    for row in cursor:
        roles.append({
            'id': row.id,
            'name': row.name,
            'value': row.value,
        })

    return jsonify(roles)


@app.route('/users/<int:user_id>', methods=['PUT'])
# @jwt_required()
# @role_required([0,1,2,3...])
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
# @jwt_required()
# @role_required([0,1,2,3...])
def delete_user(user_id):
    cursor.execute(f"DELETE FROM [user] WHERE id = {user_id}")
    conn.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


@app.route('/users', methods=['POST'])
# @jwt_required()
# @role_required([0,1,2,3...])
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
# @jwt_required()
# @role_required([0,1,2,3...])
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
# @jwt_required()
# @role_required([0,1,2,3...])
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


@app.route('/', methods=['GET'])
def home():
    msg = 'Página inicial da API de usuários em python.'
    return jsonify({"msg": msg})


if __name__ == '__main__':
    app.run(debug=True)
