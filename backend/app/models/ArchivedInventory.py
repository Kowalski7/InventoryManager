from app.extensions import db


class ArchivedInventory(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    product_name = db.Column(db.String(255))
    product_image = db.Column(db.String(255), nullable=True)
    product_barcode = db.Column(db.String(25))
    product_amount = db.Column(db.Numeric(precision=7, scale=3))
    product_remain = db.Column(db.Numeric(precision=7, scale=3))
    inventory_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.Date, nullable=True)
    base_price = db.Column(db.Numeric(precision=5, scale=2))
    modifiable = db.Column(db.Boolean())
    archived_by = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='SET NULL'), nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "product_image": self.product_image,
            "product_barcode": self.product_barcode,
            "product_amount": self.product_amount,
            "product_remain": self.product_remain,
            "inventory_date": self.inventory_date.strftime("%Y.%m.%d %H:%M"),
            "expiry_date": self.expiry_date.strftime("%Y.%m.%d") if self.expiry_date else None,
            "base_price": self.base_price,
            "modifiable": self.modifiable,
            "archived_by": self.archived_by,
            "archived_at": self.archived_at.strftime("%Y.%m.%d %H:%M") if self.archived_at else None
        }
