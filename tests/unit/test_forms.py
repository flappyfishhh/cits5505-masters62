import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from app import create_app, db
from app.forms import RegistrationForm, UploadForm
from flask_wtf.file import FileStorage
from io import BytesIO

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "testkey"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

# ====================
# Test Registration Form
# ====================

def test_registration_form_valid(app):
    with app.app_context():
        form = RegistrationForm(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            password2="password123",
            security_answer="Doggy"
        )
        assert form.validate()

def test_registration_form_password_mismatch(app):
    with app.app_context():
        form = RegistrationForm(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            password2="wrongpassword",
            security_answer="Doggy"
        )
        assert not form.validate()


# ====================
# Test Upload Form
# ====================

def test_upload_form_valid(app):
    with app.app_context():
        data = {
            "city": "Sydney",
            "latitude": -33.8688,
            "longitude": 151.2093,
            "visibility": "private",
            "share_with": ""
        }

        form = UploadForm(data=data, formdata=None, csrf_enabled=False)
        form.csv_file.data = FileStorage(
            stream=BytesIO(b"header1,header2\nvalue1,value2"),
            filename="test.csv",
            content_type="text/csv"
        )

        assert form.validate()
