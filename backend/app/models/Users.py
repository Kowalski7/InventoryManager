from app.extensions import db


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36))
    name = db.Column(db.String(50))
    username = db.Column(db.String(25))
    password = db.Column(db.String(162))
    roles = db.Column(db.JSON)

    def serialize(self):
        return {
            'id': self.id,
            'public_id': self.public_id,
            'name': self.name,
            'username': self.username,
            'roles': self.roles
        }
