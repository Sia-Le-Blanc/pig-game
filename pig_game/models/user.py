from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(16), unique = True, nullable = False)
    password = db.Column(db.String(128), nullable = False)
    chips = db.Column(db.Integer, default = 1972)