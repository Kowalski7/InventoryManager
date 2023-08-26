from flask import Blueprint, jsonify, make_response, request
from werkzeug.security import check_password_hash
import jwt
import datetime
from app.models.Users import Users
from config import Config

authentication = Blueprint('auth', __name__, url_prefix='/api/auth')


@authentication.route('', methods=['POST'])
def auth_validator():
    response_data = {
        "username": "",
        "name": "",
        "roles": [],
        "valid": False,
        "details": ""
    }
    response_code = 200

    try:
        if request.json['appBuild'] >= Config.MOBILE_APP_BUILD:
            try:
                token_data = jwt.decode(
                    request.json['token'], Config.SECRET_KEY, algorithms=['HS256'])
                user = Users.query.filter_by(
                    public_id=token_data['public_id']).first()

                if user:
                    response_data['valid'] = True
                    response_data['username'] = user.username
                    response_data['name'] = user.name
                    response_data['roles'] = user.roles
            except:
                pass
        else:
            response_data['details'] = f"You are using an outdated version of the client ({request.json['appBuild']}). Contact an administrator for information on how to update to the latest version ({Config.MOBILE_APP_BUILD})."
            response_code = 403
    except Exception as ex:
        response_data["details"] = str(ex)
        response_code = 500

    return make_response(jsonify(response_data), response_code)


@authentication.route('/login', methods=['POST'])
def auth_login():
    response = {
        "token": "",
        "success": True,
        "message": "Login successful!"
    }

    try:
        data = request.get_json()
        if not data['username'] or not data['password']:
            raise Exception("Missing required parameter.")

        user = Users.query.filter_by(username=data['username']).first()
        if user and check_password_hash(user.password, data['password']):
            token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
            ) + datetime.timedelta(weeks=4)}, Config.SECRET_KEY, "HS256")
            response['token'] = token
        else:
            raise Exception("Incorrect username or password.")

    except Exception as ex:
        response['message'] = str(ex)
        response['success'] = False

    return jsonify(response)
