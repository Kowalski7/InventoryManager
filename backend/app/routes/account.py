from flask import Blueprint, jsonify, make_response, request
from werkzeug.security import generate_password_hash

from app.middleware.tokenValidator import token_required
from app.models.Users import Users
from app.extensions import db
from app.utils import safe_uuid


account = Blueprint('user', __name__)


@account.route('/api/accounts')
@token_required
def accounts_listing(user):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    accounts = Users.query.all()
    serialized_accounts = [account.serialize() for account in accounts]

    return make_response(jsonify(sorted(serialized_accounts, key=lambda account: account['name'])))


@account.route('/api/accounts', methods=['POST'])
@token_required
def accounts_register(user):
    response = {
        "message": "Account created!",
        "success": True
    }

    try:
        data = request.get_json()
        roles = data['roles'] if 'roles' in data else ['ROLE_EMPLOYEE']
        if not data['username'] or not data['name'] or not data['password']:
            raise Exception("Missing required parameter.")

        user_query = Users.query.filter_by(username=data['username']).first()
        if user_query:
            raise Exception("A user with the same username already exists.")

        hashed_password = generate_password_hash(
            data['password'], method='scrypt')
        new_user = Users(public_id=safe_uuid(), username=data['username'],
                         name=data['name'], password=hashed_password, roles=roles)
        db.session.add(new_user)
        db.session.commit()
    except Exception as ex:
        response['message'] = str(ex)
        response['success'] = False

    return make_response(jsonify(response), 200 if response['success'] else 400)


@account.route('/api/account/<id>', methods=['PUT'])
@token_required
def account_update(user, id):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    account = Users.query.filter_by(id=id).first()
    if not account:
        return make_response(jsonify({"message": "Account not found"}), 404)

    data = request.get_json()
    for key, value in data.items():
        if value == "":
            continue
        if key != 'password':
            setattr(account, key, value)
        else:
            account.password = generate_password_hash(value, method='scrypt')
            account.public_id = safe_uuid()

    db.session.commit()

    return make_response(jsonify({"message": "Account updated!"}), 200)


@account.route('/api/account/<id>', methods=['DELETE'])
@token_required
def account_delete(user, id):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    account = Users.query.filter_by(id=id).first()
    if not account:
        return make_response(jsonify({"message": "Account not found"}), 404)

    db.session.delete(account)
    db.session.commit()

    return make_response(jsonify({"message": "Account deleted!"}), 200)


@account.route('/api/account/change_password', methods=['POST'])
@token_required
def account_change_password(user):
    data = request.get_json()
    if data.get('new_password') in [None, '']:
        return make_response(jsonify({"message": "Missing required parameter"}), 400)

    user.password = generate_password_hash(
        data['new_password'], method='scrypt')
    user.public_id = safe_uuid()

    db.session.commit()

    return make_response(jsonify({"message": "Password changed!"}), 200)
