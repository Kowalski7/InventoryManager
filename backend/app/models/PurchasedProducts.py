from app.extensions import db


class PurchasedProducts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey(
        'transactions.id'))
    product_name = db.Column(db.String(255))
    item_count = db.Column(db.Numeric(precision=7, scale=3))
    payed_price = db.Column(db.Numeric(precision=6, scale=2))

    def serialize(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "product_name": self.product_name,
            "item_count": self.item_count,
            "payed_price": self.payed_price
        }
