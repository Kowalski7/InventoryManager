from flask import Blueprint, jsonify, make_response
from sqlalchemy import func, and_
from app.middleware.tokenValidator import token_required

from app.modules.management_suggestions import get_suggestion
from app.utils import get_quantity_from_barcode, query_product_by_barcode


product_lookup = Blueprint('product_lookup', __name__,
                           url_prefix='/api/product_lookup')


@product_lookup.route('/<barcode>/detailed')
@token_required
def product_lookup_by_barcode(user, barcode):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    response = {
        'product_name': '',
        'product_barcode': '',
        'total_quantity': 0,
        'total_remain': 0,
        'base_product_price': 0,
        'active_product_price': 0,
        'scanned_product_price': 0,
        'oldest_lot_date': '',
        'newest_lot_date': '',
        'price_changes': [],
        'inventory': [],
        'out_of_stock_prediction': ''
    }

    # ? Search for the product by barcode
    inventory_lookup, changes_lookup = query_product_by_barcode(barcode)
    if not inventory_lookup:
        return make_response(jsonify({"message": "Product not found!"}), 404)

    response['product_name'] = inventory_lookup[0][0].product_name
    response['product_barcode'] = inventory_lookup[0][0].product_barcode
    response['total_quantity'] = sum(
        [item[0].product_amount for item in inventory_lookup])
    response['total_remain'] = sum(
        [item[0].product_remain for item in inventory_lookup])
    response['base_product_price'] = inventory_lookup[0][0].base_price

    # #? If there's a price change for the product
    # if changes_lookup:
    #     #? If the product has a variable quantity
    #     if changes_lookup[0] != barcode:
    #         response['scanned_product_price'] = changes_lookup[1] * get_quantity_from_barcode(barcode)
    #     else:
    #         response['scanned_product_price'] = changes_lookup[1]
    # else:
    #     #? If the product has a variable quantity
    #     if inventory_lookup[0][0].product_barcode != barcode:
    #         response['scanned_product_price'] = inventory_lookup[0][0].base_price * get_quantity_from_barcode(barcode)
    #     else:
    #         response['scanned_product_price'] = inventory_lookup[0][0].base_price

    # ? Get the scanned product's price (which can either be the base or a modified one) and muliply it by the quantity if the product has a variable quantity
    response['scanned_product_price'] = round((changes_lookup[1] if changes_lookup else response['base_product_price']) * (
        get_quantity_from_barcode(barcode) if barcode not in [response['product_barcode'], changes_lookup[0] if changes_lookup else None] else 1), 2)

    # ? Get the active product-wide price
    for item in inventory_lookup:
        if item[1] and item[1].modification_barcode == response['product_barcode']:
            response['active_product_price'] = item[1].new_price
            break
    else:
        response['active_product_price'] = response['base_product_price']

    response['oldest_lot_date'] = inventory_lookup[-1][0].inventory_date
    response['newest_lot_date'] = inventory_lookup[0][0].inventory_date

    # ? Get the price changes & inventory
    for item in inventory_lookup:
        if item[1] is not None:
            change = item[1].serialize()
            change['approved_by_name'] = item[2]
            change['approved_by_username'] = item[3]
            response['price_changes'].append(change)

        response['inventory'].append(item[0].serialize())

    response['out_of_stock_prediction'] = get_suggestion(
        inventory_lookup[0][0]).out_of_stock_prediction

    return make_response(jsonify(response))


@product_lookup.route('/<barcode>')
def product_lookup_by_barcode_short(barcode):
    response = {
        'product_name': '',
        'product_barcode': '',
        'total_quantity': 0,
        'total_remain': 0,
        'base_product_price': 0,
        'active_product_price': 0,
        'scanned_product_price': 0
    }

    # ? Search for the product by barcode
    inventory_lookup, changes_lookup = query_product_by_barcode(barcode)
    if not inventory_lookup:
        return make_response(jsonify({"message": "Product not found!"}), 404)

    response['product_name'] = inventory_lookup[0][0].product_name
    response['product_barcode'] = inventory_lookup[0][0].product_barcode
    response['total_quantity'] = sum(
        [item[0].product_amount for item in inventory_lookup])
    response['total_remain'] = sum(
        [item[0].product_remain for item in inventory_lookup])
    response['base_product_price'] = inventory_lookup[0][0].base_price
    response['scanned_product_price'] = round((changes_lookup[1] if changes_lookup else response['base_product_price']) * (
        get_quantity_from_barcode(barcode) if barcode not in [response['product_barcode'], changes_lookup[0] if changes_lookup else None] else 1), 2)

    return make_response(jsonify(response))
