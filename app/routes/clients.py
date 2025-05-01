from flask import jsonify, request
from werkzeug.security import generate_password_hash
from app import db
from app.models import Client
from app.routes import bp
from app.auth import token_required

@bp.route('/clients', methods=['GET'])
@token_required
def get_clients(current_user):
    client_id = request.args.get('client_id')

    if client_id:
        try:
            client = Client.query.get_or_404(client_id)
            return jsonify(client.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            clients = Client.query.all()
            return jsonify([client.to_dict() for client in clients]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@bp.route('/clients', methods=['POST'])
@token_required
def create_client(current_user):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied. Admins only.'}), 403

    try:
        data = request.get_json() or {}

        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password.'}), 400

        if Client.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists.'}), 400

        hashed_password = generate_password_hash(data['password'])

        client = Client(
            username=data['username'],
            password=hashed_password,
            name=data.get('name', ''),
            email=data.get('email', ''),
            icon=data.get('icon', 'static/icons/default.png'),
            is_admin=data.get('is_admin', False)  # Só você (admin) pode definir isso
        )
        db.session.add(client)
        db.session.commit()
        return jsonify(client.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/clients/<int:id>', methods=['PUT'])
@token_required
def update_client(current_user, id):
    client = Client.query.get_or_404(id)

    if current_user.id != client.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}

    if 'username' in data:
        existing_user = Client.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != client.id:
            return jsonify({'error': 'Username already exists.'}), 400
        client.username = data['username']

    if 'password' in data:
        client.password = generate_password_hash(data['password'])

    if 'name' in data:
        client.name = data['name']
    if 'email' in data:
        client.email = data['email']
    if 'icon' in data:
        client.icon = data['icon']

    db.session.commit()
    return jsonify(client.to_dict()), 200

@bp.route('/clients/<int:id>', methods=['DELETE'])
@token_required
def delete_client(current_user, id):
    client = Client.query.get_or_404(id)

    if current_user.id != client.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(client)
    db.session.commit()
    return jsonify({'message': 'Client deleted'}), 200
@bp.route('/clients/register', methods=['POST'])
def register_client():
    try:
        data = request.get_json() or {}

        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password.'}), 400

        if Client.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists.'}), 400

        hashed_password = generate_password_hash(data['password'])

        client = Client(
            username=data['username'],
            password=hashed_password,
            name=data.get('name', ''),
            email=data.get('email', ''),
            icon=data.get('icon', 'static/icons/default.png'),
            is_admin=False
        )
        db.session.add(client)
        db.session.commit()
        return jsonify(client.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


