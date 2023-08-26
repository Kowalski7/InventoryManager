from app.models.Inventory import Inventory
from app.extensions import db


def remove_empty_lots():
    lots = Inventory.query.with_entities(Inventory).filter(
        Inventory.product_remain == 0).all()

    for lot in lots:
        db.session.delete(lot)

    db.session.commit()
