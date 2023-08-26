from app.extensions import db


class SuggestedModifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.String(36), db.ForeignKey(
        'inventory.id', ondelete='SET NULL'))
    type = db.Column(
        db.Enum('PriceIncrease', 'PriceDecrease', 'Restock', 'Dispose'))
    new_price = db.Column(db.Numeric(precision=5, scale=2), nullable=True)
    out_of_stock_prediction = db.Column(db.Date, nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "inventory_id": self.inventory_id,
            "type": self.type,
            "new_price": self.new_price,
            "out_of_stock_prediction": self.out_of_stock_prediction
        }
