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


class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(256), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    city = db.Column(db.String(100), nullable=False)           
    latitude = db.Column(db.Float, nullable=False)              
    longitude = db.Column(db.Float, nullable=False)             
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='files')
    uploads = db.relationship('Upload', back_populates='file', cascade='all, delete-orphan')


class Upload(db.Model):
    __tablename__ = 'uploads'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=False, index=True)
    row_number = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON, nullable=False)

    file = db.relationship('FileUpload', back_populates='uploads')
