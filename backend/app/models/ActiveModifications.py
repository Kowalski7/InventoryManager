from app.extensions import db


class ActiveModifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.String(36), db.ForeignKey(
        'inventory.id', ondelete='CASCADE'))
    approved_by = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='SET NULL'), nullable=True)
    approved_at = db.Column(db.DateTime)
    automatic = db.Column(db.Boolean(), default=False)
    new_price = db.Column(db.Numeric(precision=5, scale=2))
    modification_barcode = db.Column(db.String(25), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "inventory_id": self.inventory_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.strftime("%Y.%m.%d %H:%M") if self.approved_at else None,
            "automatic": self.automatic,
            "new_price": self.new_price,
            "modification_barcode": self.modification_barcode
        }
