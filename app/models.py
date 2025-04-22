from datetime import datetime
from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    security_answer_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    files = db.relationship('FileUpload', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_security_answer(self, answer):
        # Normalize and hash the security answer
        self.security_answer_hash = generate_password_hash(answer.strip().lower())

    def check_security_answer(self, answer):
        return check_password_hash(self.security_answer_hash, answer.strip().lower())