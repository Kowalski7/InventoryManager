from datetime import datetime
from flask import Blueprint, jsonify, make_response, request

from app.middleware.tokenValidator import token_required
from app.models.ActiveModifications import ActiveModifications
from app.models.SuggestedModifications import SuggestedModifications
from app.models.Inventory import Inventory
from app.modules.management_suggestions import generate_suggestions, get_suggestion
from app.utils import generate_code128_barcode
import app.extensions as ext
from config import Config

suggestions = Blueprint('suggestions', __name__, url_prefix='/api/suggestions')


@suggestions.route('')
@token_required
def get_suggestions(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    properties = ['id', 'inventory_id', 'type', 'new_price', 'out_of_stock_prediction', 'base_price',
                  'inventory_date', 'expiry_date', 'product_amount', 'product_remain', 'product_name', 'product_barcode']
    result = SuggestedModifications.query.with_entities(SuggestedModifications.id, SuggestedModifications.inventory_id, SuggestedModifications.type, SuggestedModifications.new_price, SuggestedModifications.out_of_stock_prediction,
                                                        Inventory.base_price, Inventory.inventory_date, Inventory.expiry_date, Inventory.product_amount, Inventory.product_remain, Inventory.product_name, Inventory.product_barcode).join(Inventory, (SuggestedModifications.inventory_id == Inventory.id)).all()

    serialized_result = []
    for i in result:
        serialized_item = dict(zip(properties, i))
        serialized_item['inventory_date'] = serialized_item['inventory_date'].strftime(
            "%Y.%m.%d %H:%M")
        serialized_item['expiry_date'] = serialized_item['expiry_date'].strftime(
            "%Y.%m.%d")
        if serialized_item['out_of_stock_prediction'] is not None:
            serialized_item['out_of_stock_prediction'] = serialized_item['out_of_stock_prediction'].strftime(
                "%Y.%m.%d")
        serialized_result.append(serialized_item)

    return make_response(jsonify(serialized_result))


@suggestions.route('', methods=['POST'])
@token_required
def request_suggestions(user):
    if not user or not set(user.roles).intersection(['ROLE_EMPLOYEE', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    if request.args.get('lot') is not None:
        lot = Inventory.query.filter_by(id=request.args.get('lot')).first()
        if lot is None:
            return make_response(jsonify({"message": "Lot not found"}), 404)

        return make_response(jsonify(get_suggestion(lot).serialize()))
    else:
        if request.args.get('sync') == "true":
            generate_suggestions()
            return make_response(jsonify({"message": "Suggestions generated"}), 200)
        else:
            ext.task_scheduler.queue_task_asap("auto_suggestions")
            return make_response(jsonify({"message": "Regenerating suggestions..."}), 202)


@suggestions.route('/<id>/apply', methods=['POST'])
@token_required
def accept_suggestion(user, id):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    suggestion = SuggestedModifications.query.filter_by(id=id).first()
    if suggestion is None:
        return make_response(jsonify({"message": "Suggestion not found"}), 404)

    if suggestion.type in ['PriceIncrease', 'PriceDecrease']:
        change = ActiveModifications(
            inventory_id=suggestion.inventory_id,
            new_price=suggestion.new_price,
            approved_by=user.id,
            approved_at=datetime.now().strftime("%Y.%m.%d %H:%M"),
            modification_barcode=generate_code128_barcode(
                Config.INTERNAL_NUMBER)
        )

        ext.db.session.add(change)
        ext.db.session.delete(suggestion)
        ext.db.session.commit()
        return make_response(jsonify({"message": "Suggestion applied successfully"}))

    else:
        return make_response(jsonify({"message": "Not implemented"}), 501)


@suggestions.route('', methods=['DELETE'])
@token_required
def delete_suggestions(user):
    if not user or not set(user.roles).intersection(['ROLE_MANAGER', 'ROLE_DEVELOPER']):
        return make_response(jsonify({"message": "Forbidden"}), 403)

    SuggestedModifications.query.delete()
    ext.db.session.commit()
    return make_response(jsonify({"message": "Suggestions deleted"}))
