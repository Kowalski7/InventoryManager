from decimal import Decimal
from random import randint

from sqlalchemy import and_, or_

from app.models.ActiveModifications import ActiveModifications
from app.models.Inventory import Inventory
from app.models.Users import Users


def query_product_by_barcode(barcode: str) -> tuple:
    # ? Check to see if the given barcode is an active change barcode instead of a product barcode
    changes_lookup = ActiveModifications.query.with_entities(Inventory.product_barcode, ActiveModifications.new_price).filter(or_(ActiveModifications.modification_barcode == barcode, and_(ActiveModifications.modification_barcode.like(
        "%00000_"), ActiveModifications.modification_barcode.startswith(barcode[:-6])))).join(Inventory, (ActiveModifications.inventory_id == Inventory.id)).order_by(ActiveModifications.approved_at.desc()).first()

    if changes_lookup:
        barcode = changes_lookup[0]

    # ? Search for the product by barcode
    inventory_lookup = Inventory.query.with_entities(Inventory, ActiveModifications, Users.name, Users.username).filter(or_(Inventory.product_barcode == barcode, and_(Inventory.product_barcode.like("%00000_"), Inventory.product_barcode.startswith(
        barcode[:-6])))).outerjoin(ActiveModifications, (Inventory.id == ActiveModifications.inventory_id)).outerjoin(Users, (ActiveModifications.approved_by == Users.id)).order_by(Inventory.inventory_date.desc()).all()

    return (inventory_lookup, changes_lookup)


def safe_uuid(max_attempts: int = 10) -> str:
    import uuid
    from app.models.Users import Users

    for _ in range(max_attempts):
        unique_uuid = str(uuid.uuid4())
        if Users.query.filter_by(public_id=unique_uuid).first() is None:
            break
    else:
        raise Exception("Could not generate a unique UUID.")
    return unique_uuid


def generate_code128_barcode(internal_number: int, var_qty: bool) -> str:
    assert internal_number in range(
        1, 10), "Internal number must be between 1 and 9."
    if var_qty:
        return f"5{internal_number}{randint(1000000, 9999999)}000002"
    return f"5{internal_number}{randint(100000000000, 999999999999)}1"


def get_quantity_from_barcode(barcode: str) -> Decimal:
    return Decimal(barcode[-6:len(barcode)-1]) / Decimal(1000)
