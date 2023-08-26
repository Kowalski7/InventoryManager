from io import BytesIO
import os
from glob import glob
from flask import Blueprint, jsonify, make_response, redirect, request, send_file

from app.middleware.tokenValidator import token_required
from app.models.Inventory import Inventory
from config import Config
from PIL import Image


inv_images = Blueprint('inv_imgs', __name__)

ALLOWED_TYPES = {'image/jpeg': 'jpeg', 'image/png': 'png'}


def file_extension(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower()


@inv_images.route('/api/inventory/<id>/image', methods=['POST'])
@token_required
def upload_image(user, id):
    filedata = request.get_data()

    if not filedata:
        return make_response(jsonify({"message": "No file data received"}), 400)

    lot = Inventory.query.filter_by(id=id).first()
    if lot is None:
        return make_response(jsonify({"message": f"Lot with ID '{id}' not found"}), 404)

    if request.content_type in ALLOWED_TYPES.keys():
        filename = f"{id}.{ALLOWED_TYPES[request.content_type]}"
        with open(os.path.join(Config.UPLOAD_FOLDER, filename), 'wb') as file:
            resized = Image.open(BytesIO(filedata)).convert('RGB')
            resized.thumbnail((500, 500))
            resized.save(file, optimize=True, quality=80,
                         format=ALLOWED_TYPES[request.content_type])
        return make_response(jsonify({"message": "File uploaded", "filename": filename}), 200)

    return make_response(jsonify({"message": f"Unsupported media type '{request.content_type}'"}), 400)


@inv_images.route('/api/inventory/<id>/image', methods=['GET'])
def get_image(id):
    lot = Inventory.query.filter_by(id=id).first()
    if lot is None:
        return make_response(jsonify({"message": f"Lot with ID '{id}' not found"}), 404)

    filename = lot.product_image

    if filename and filename != "internal":
        return redirect(filename)
    elif not filename:
        return make_response(send_file(f"{os.getcwd()}/{Config.UPLOAD_FOLDER}fallback.jpg"), 200)

    file_search = glob(f"{Config.UPLOAD_FOLDER}{id}.*")

    if len(file_search) == 0:
        return make_response(send_file(f"{os.getcwd()}/{Config.UPLOAD_FOLDER}fallback.jpg"), 200)

    return make_response(send_file(os.getcwd() + "/" + file_search[0]), 200)
