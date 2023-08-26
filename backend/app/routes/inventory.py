from datetime import datetime, date
from glob import glob
import os
import uuid
from flask import Blueprint, jsonify, make_response, request
from sqlalchemy import desc, or_
from app.models.Inventory import Inventory
import json

from app.middleware.tokenValidator import token_required
from app.extensions import db
from config import Config


inventory = Blueprint('inventory', __name__, url_prefix='/api/inventory')

sort_options = {
    'id': Inventory.id,
    'product_name': Inventory.product_name,
    'inventory_date': Inventory.inventory_date,
    'expiry_date': Inventory.expiry_date,
    'quantity_lot': Inventory.product_amount,
    'quantity_left': Inventory.product_remain,
    'price': Inventory.base_price,
}


@inventory.route('')
@token_required
def inventory_listing(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    #! Date filtering
    if 'dateFrom' in request.args or 'dateTo' in request.args:
        dateFrom = request.args.get(
            'dateFrom') if 'dateFrom' in request.args else datetime.min
        dateTo = request.args.get(
            'dateTo') if 'dateTo' in request.args else date.today()

        result = Inventory.query.filter(Inventory.inventory_date.between(
            dateFrom, dateTo))
    else:
        result = Inventory.query

    #! Searching
    if 'search' in request.args:
        result = result.filter(or_(Inventory.product_name.contains(
            request.args['search']), Inventory.id.contains(request.args['search'])))

    #! Sorting
    if request.args.get('sort_by') in sort_options:
        sort_by = sort_options[request.args.get('sort_by')]
        if request.args.get('sort_order') == 'desc':
            sort_by = desc(sort_by)
        result = result.order_by(sort_by)

    #! Pagination
    if 'limit' in request.args and 'offset' in request.args:
        result = result.limit(int(request.args['limit'])).offset(
            int(request.args['offset']))

    serialized_result = [item.serialize() for item in result.all()]

    return make_response(jsonify(serialized_result))


@inventory.route('/<id>')
@token_required
def inventory_item(user, id):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    result = Inventory.query.filter_by(id=id).first()

    if result is None:
        return make_response(jsonify({"message": f"Lot with ID '{id}' not found"}), 404)

    return make_response(jsonify(result.serialize()))


@inventory.route('', methods=['POST'])
@token_required
def inventory_insert(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    data = request.get_json()
    new_product = Inventory(
        id=str(uuid.uuid4()),
        product_name=data['product_name'],
        product_image=data['product_image'] if 'product_image' in data else None,
        product_barcode=data['product_barcode'],
        product_amount=data['product_amount'],
        product_remain=data['product_remain'],
        inventory_date=datetime.strptime(
            data['inventory_date'], "%Y.%m.%d %H:%M"),
        expiry_date=datetime.strptime(
            data['expiry_date'], "%Y.%m.%d").date() if 'expiry_date' in data else None,
        base_price=data['base_price'],
        modifiable=data['modifiable'],
        added_by=user.id,
        modified_by=None,
        modified_at=datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    )

    db.session.add(new_product)
    db.session.commit()

    return make_response(jsonify(new_product.serialize()), 201)


@inventory.route('/<id>', methods=['PUT'])
@token_required
def inventory_update(user, id):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    data = request.get_json()
    lot = inventory.query.filter_by(id=id).first()

    # update only the fields that are not empty
    for key, value in data.items():
        if value:
            if key in ['inventory_date', 'expiry_date']:
                # convert date strings to datetime and date objects
                value = datetime.strptime(value, "%Y.%m.%d %H:%M") if key == 'inventory_date' else datetime.strptime(
                    value, "%Y.%m.%d").date()
            if key in ['added_by', 'modified_by', 'modified_at']:
                # ignore these fields as they should not be modifiable by the user
                continue
            setattr(lot, key, value)

    lot.modified_by = user.id
    lot.modified_at = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    db.session.commit()

    return make_response(jsonify(lot.serialize()), 201)


@inventory.route('/<id>', methods=['DELETE'])
@token_required
def inventory_delete(user, id):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    lot = Inventory.query.filter_by(id=id).first()

    if lot is None:
        return make_response(jsonify({"message": f"Lot with ID '{id}' not found"}), 404)

    file_search = glob(f"{Config.UPLOAD_FOLDER}{id}.*")
    try:
        for file in file_search:
            os.remove(file)
    except:
        pass

    db.session.delete(lot)
    db.session.commit()

    return make_response(jsonify({"message": f"Lot with ID '{id}' deleted"}), 418)
