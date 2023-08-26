from flask import jsonify, make_response, request
from functools import wraps
import jwt
from app.models.Users import Users
from config import Config


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        else:
            token = request.args.get('token')

        if not token:
            return make_response(jsonify({'message': 'a valid token is missing'}), 401)

        try:
            data = jwt.decode(
                token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = Users.query.filter_by(
                public_id=data['public_id']).first()
            assert (current_user is not None)
        except:
            return make_response(jsonify({'message': 'token is invalid'}), 401)

        if len(current_user.roles) == 0:
            return make_response(jsonify({'message': 'user has no roles'}), 401)

        return f(current_user, *args, **kwargs)
    return decorator
