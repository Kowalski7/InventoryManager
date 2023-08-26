from app.extensions import db


class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    total_price = db.Column(db.Numeric(precision=7, scale=2))

    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "total_price": self.total_price
        }
