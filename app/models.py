from datetime import datetime
from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# ================================
# User model
# ================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    security_answer_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # One-to-many: user owns many uploaded files
    files = db.relationship('FileUpload', back_populates='user', cascade='all, delete-orphan')

    # Many-to-many: files shared with this user
    shared_files = db.relationship('FileUpload', secondary='file_share', back_populates='share_with')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_security_answer(self, answer):
        # Normalize and hash the security answer (case and space insensitive)
        self.security_answer_hash = generate_password_hash(answer.strip().lower())

    def check_security_answer(self, answer):
        return check_password_hash(self.security_answer_hash, answer.strip().lower())


# ================================
# File upload model
# ================================
class FileUpload(db.Model):
    __tablename__ = 'file_uploads'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(256), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)

    # Location metadata
    city = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # File visibility: 'private' (default), 'public', or 'shared'
    visibility = db.Column(db.String(10), default='private')

    # Many-to-many: users the file is shared with
    share_with = db.relationship('User', secondary='file_share', back_populates='shared_files')

    # Back reference to the uploading user
    user = db.relationship('User', back_populates='files')

    # One-to-many: each file has multiple uploaded data rows
    uploads = db.relationship('Upload', back_populates='file', cascade='all, delete-orphan')


# ================================
# File share association table
# (many-to-many between User and FileUpload)
# ================================
class FileShare(db.Model):
    __tablename__ = 'file_share'

    file_id = db.Column(db.Integer, db.ForeignKey('file_uploads.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)


# ================================
# Upload record model
# (each record is one row of uploaded CSV data)
# ================================
class Upload(db.Model):
    __tablename__ = 'uploads'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=False, index=True)
    row_number = db.Column(db.Integer, nullable=False)  # Preserves row order
    data = db.Column(db.JSON, nullable=False)  # Raw row data stored as JSON

    # Link back to parent file
    file = db.relationship('FileUpload', back_populates='uploads')
