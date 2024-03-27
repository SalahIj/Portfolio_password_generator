from datetime import datetime
from pass_gn import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    passwords = db.relationship('Password', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    
class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_generated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    password = db.Column(db.String(100), nullable=False)
    include_numbers = db.Column(db.Boolean, nullable=False)
    include_lowercase = db.Column(db.Boolean, nullable=False)
    include_uppercase = db.Column(db.Boolean, nullable=False)
    include_symbols = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"Password('{self.date_generated}', '{self.password}', '{self.include_numbers}', '{self.include_lowercase}', '{self.include_uppercase}', '{self.include_symbols}')"
