from datetime import datetime
import json
import re
from flask import Blueprint, jsonify, make_response, request
from sqlalchemy import desc, or_

from app.extensions import db
from app.middleware.tokenValidator import token_required
from app.models.ActiveModifications import ActiveModifications
from app.models.Inventory import Inventory
from app.models.Users import Users
from app.utils import generate_code128_barcode
from config import Config


price_changes = Blueprint('price_changes', __name__,
                          url_prefix='/api/price_changes')


@price_changes.route('')
@token_required
def price_changes_listing(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    result = ActiveModifications.query.with_entities(ActiveModifications, Inventory.product_name, Inventory.product_barcode, Users.name).join(Inventory, (Inventory.id == ActiveModifications.inventory_id)).order_by(
        ActiveModifications.approved_at.desc()).join(Users, (Users.id == ActiveModifications.approved_by), isouter=True).all()

    # return make_response(str(result), 200)

    serialized_result = []
    for item in result:
        serialized_item = item[0].serialize()
        serialized_item['product_name'] = item[1]
        serialized_item['is_lot_level'] = item[2] == serialized_item['modification_barcode']
        serialized_item['approved_by'] = item[3]
        serialized_result.append(serialized_item)

    return make_response(jsonify(serialized_result))


@price_changes.route('', methods=['POST'])
@token_required
def price_changes_add(user):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    has_variable_qty = re.compile(r"^[0-9]+(00000)[0-9]{1}$")
    data = request.get_json()

    if not 'inventory_id' in data or not 'new_price' in data:
        return make_response(jsonify({"message": "Missing required fields"}), 400)

    inventory = Inventory.query.filter_by(
        id=data['inventory_id']).first()

    if not inventory:
        return make_response(jsonify({"message": "Lot not found"}), 404)

    old_change = ActiveModifications.query.filter_by(
        inventory_id=data['inventory_id']).first()
    if old_change:
        db.session.delete(old_change)

    new_price_change = ActiveModifications(
        inventory_id=data['inventory_id'],
        new_price=data['new_price'],
        modification_barcode=generate_code128_barcode(Config.INTERNAL_NUMBER, has_variable_qty.match(inventory.product_barcode)) if data.get(
            'modification_barcode') == True else inventory.product_barcode,
        approved_by=user.id,
        approved_at=datetime.now().strftime("%Y.%m.%d %H:%M:%S"),
        automatic=False
    )

    db.session.add(new_price_change)
    db.session.commit()

    return make_response(jsonify({"message": "Price change added"}), 201)


@price_changes.route('/<id>', methods=['DELETE'])
@token_required
def price_changes_delete(user, id):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    price_change = ActiveModifications.query.filter_by(id=id).first()

    if not price_change:
        return make_response(jsonify({"message": "Price change not found"}), 404)

    db.session.delete(price_change)
    db.session.commit()

    return make_response(jsonify({"message": "Price change deleted"}), 200)
