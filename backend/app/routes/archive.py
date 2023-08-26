from datetime import datetime
from flask import Blueprint, jsonify, make_response, request

from app.middleware.tokenValidator import token_required
from app.models.ArchivedInventory import ArchivedInventory
from app.extensions import db
from app.models.Inventory import Inventory


archive = Blueprint('archive', __name__, url_prefix='/api/archive')


@archive.route('')
@token_required
def get_archive(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    archived_inventory = ArchivedInventory.query.order_by(
        ArchivedInventory.archived_at.desc()).all()

    serialized_result = [archived.serialize()
                         for archived in archived_inventory]

    return make_response(jsonify(serialized_result))


@archive.route('/<id>')
@token_required
def get_archive_by_id(user, id):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    archived_inventory = ArchivedInventory.query.filter_by(id=id).first()

    if not archived_inventory:
        return make_response(jsonify({"message": "Archived item not found"}), 404)

    serialized_result = archived_inventory.serialize()

    return make_response(jsonify(serialized_result))


@archive.route('/<id>', methods=['DELETE'])
@token_required
def delete_archive_by_id(user, id):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    archived_inventory = ArchivedInventory.query.filter_by(id=id).first()

    if not archived_inventory:
        return make_response(jsonify({"message": "Archived item not found"}), 404)

    db.session.delete(archived_inventory)
    db.session.commit()

    return make_response(jsonify({"message": "Archived item deleted"}), 200)


@archive.route('', methods=['POST'])
@token_required
def add_archive(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    data = request.get_json()

    if not 'inventory_id' in data:
        return make_response(jsonify({"message": "Missing required fields"}), 400)

    inventory = Inventory.query.filter_by(
        id=data['inventory_id']).first()

    if not inventory:
        return make_response(jsonify({"message": "Lot not found"}), 404)

    #! Check if there's already an archived item with the same inventory_id and delete it
    archived_inventory = ArchivedInventory.query.filter_by(
        id=data['inventory_id']).first()
    if archived_inventory:
        db.session.delete(archived_inventory)

    new_archive = ArchivedInventory(
        id=inventory.id,
        product_name=inventory.product_name,
        product_barcode=inventory.product_barcode,
        base_price=inventory.base_price,
        product_amount=inventory.product_amount,
        product_remain=inventory.product_remain,
        inventory_date=inventory.inventory_date,
        expiry_date=inventory.expiry_date,
        modifiable=inventory.modifiable,
        archived_by=user.id,
        archived_at=datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    )

    db.session.delete(inventory)
    db.session.add(new_archive)
    db.session.commit()

    return make_response(jsonify({"message": "Item archived successfully!"}), 200)
