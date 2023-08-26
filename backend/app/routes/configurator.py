import json
from flask import Blueprint, jsonify, make_response, request

from app.middleware.tokenValidator import token_required
import app.extensions as extensions
from config import Config


configurator = Blueprint('configurator', __name__,
                         url_prefix='/api/configurator')


@configurator.route('')
@token_required
def configurator_get(user):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    try:
        with open('config.json', 'r') as file:
            return make_response(json.loads(file.read()), 200)
    except Exception as ex:
        return make_response({"message": str(ex)}, 500)


@configurator.route('', methods=['POST'])
@token_required
def configurator_save(user):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response({"message": "Forbidden"}, 403)

    try:
        data = request.get_json()
        with open('config.json', 'w') as file:
            file.write(json.dumps(data))
        Config.CONFIG_DATA = data
        extensions.task_scheduler.stop()
        extensions.task_scheduler.start()
        return make_response({"message": "Configuration applied"}, 200)
    except Exception as ex:
        return make_response({"message": str(ex)}, 500)
