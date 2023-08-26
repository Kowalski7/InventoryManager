from flask import Blueprint, jsonify, make_response


tests = Blueprint('tests', __name__, url_prefix='/api/tests')


@tests.route('/ping')
def ping():
    return make_response(jsonify({"message": "pong"}), 200)
