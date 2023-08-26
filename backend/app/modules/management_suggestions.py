from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import and_, func, text

from app.extensions import db
from app.models.Inventory import Inventory
from app.models.SuggestedModifications import SuggestedModifications
from app.models.PurchasedProducts import PurchasedProducts
from app.models.Transactions import Transactions
from config import Config


# (id, product_name, product_barcode, product_amount, product_remain, inventory_date, expiry_date, base_price)
# THRESHOLD_PRICE_INCREASE = 0.7
# THRESHOLD_PRICE_DECREASE = -0.4
# PRICE_INCREASE_MULTIPLIER = 0.12
# PRICE_DECREASE_MULTIPLIER = 0.2
# RESTOCK_DAYS_THRESHOLD = 7


def quantity_until_expiry_ratio(lot: Inventory) -> float:
    return Decimal((lot.expiry_date - date.today()).days / (lot.expiry_date - lot.inventory_date.date()).days) - (lot.product_remain / lot.product_amount)


def product_demand_frequency(lot: Inventory) -> float:
    transactions = Transactions.query.with_entities(PurchasedProducts.transaction_id, PurchasedProducts.product_name, PurchasedProducts.item_count, Transactions.date).join(
        Transactions, Transactions.id == PurchasedProducts.transaction_id).filter(PurchasedProducts.product_name == lot.product_name).order_by(Transactions.date.asc()).all()

    # print(f"DEBUG: Found {len(transactions)} transactions for {lot.product_name}!")

    last_date = lot.inventory_date
    delta_times = []    # in hours
    total_qty = 0
    for transaction in transactions:
        difference = transaction.date - last_date
        delta_times.append(
            (difference.days * 86400 + difference.seconds) / 3600)
        total_qty += transaction.item_count
        last_date = transaction.date

    difference = datetime.now() - last_date
    delta_times.append((difference.days * 86400 + difference.seconds) / 3600)
    # print(f"DEBUG: delta_times: {delta_times}")

    return sum(delta_times) / float(total_qty) if len(delta_times) > 1 else -1


def get_suggestion(lot: Inventory) -> SuggestedModifications:
    days_until_expiry = (lot.expiry_date - date.today()).days

    result = SuggestedModifications(
        inventory_id=lot.id,
        type=None,
        new_price=0,
        out_of_stock_prediction=None
    )

    if days_until_expiry <= 0:
        result.type = "Dispose"
    else:
        qty_exp = quantity_until_expiry_ratio(lot)
        avg_delta = product_demand_frequency(lot)
        time_until_oos = timedelta(
            days=((float(lot.product_remain) * avg_delta) / 24))
        result.out_of_stock_prediction = date.today() + time_until_oos

        if time_until_oos.days <= Config.CONFIG_DATA["threshold_restock_days"] and time_until_oos.days > -1:
            result.type = "Restock"
        else:
            if qty_exp >= Config.CONFIG_DATA["threshold_price_increase"]:
                result.type = "PriceIncrease"
                result.new_price = lot.base_price + \
                    lot.base_price * \
                    (qty_exp *
                     Decimal(Config.CONFIG_DATA["multiplier_price_increase"]))
            elif qty_exp <= Config.CONFIG_DATA["threshold_price_decrease"]:
                result.type = "PriceDecrease"
                result.new_price = lot.base_price + \
                    lot.base_price * \
                    (qty_exp *
                     Decimal(Config.CONFIG_DATA["multiplier_price_decrease"]))

    return result


def generate_suggestions():
    lots = Inventory.query.filter(and_(Inventory.modifiable == True, and_(date.today() >= (func.date_add(Inventory.inventory_date, text("INTERVAL (%s/2) DAY" % func.datediff(
        Inventory.expiry_date, Inventory.inventory_date)))), Inventory.id.not_in(SuggestedModifications.query.with_entities(SuggestedModifications.inventory_id)))))

    SuggestedModifications.query.delete()

    for lot in lots:
        db.session.add(get_suggestion(lot))

    db.session.commit()
