import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from app import create_app, db
from app.models import User, FileUpload

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db.session

# ====================
# Test User model
# ====================

def test_user_password_hashing(db_session):
    user = User(username='testuser', email='test@example.com')
    user.set_password('mysecret')
    user.set_security_answer('fluffy')
    db_session.add(user)
    db_session.commit()

    retrieved = User.query.filter_by(username='testuser').first()
    assert retrieved is not None
    assert retrieved.check_password('mysecret')
    assert not retrieved.check_password('wrongpassword')

def test_user_security_answer(db_session):
    user = User(username='test2', email='test2@example.com')
    user.set_password('testpass')
    user.set_security_answer('Fluffy')
    db_session.add(user)
    db_session.commit()

    retrieved = User.query.filter_by(username='test2').first()
    assert retrieved.check_security_answer('fluffy')  # case-insensitive
    assert not retrieved.check_security_answer('wrong')

# ====================
# Test FileUpload model
# ====================

def test_fileupload_creation(db_session):
    user = User(username='uploader', email='upload@example.com')
    user.set_password('pass')
    user.set_security_answer('answer')
    db_session.add(user)
    db_session.commit()

    file = FileUpload(
        filename='data.csv',
        filepath='/path/to/data.csv',
        city='Perth',
        latitude=-31.9505,
        longitude=115.8605,
        user_id=user.id
    )
    db_session.add(file)
    db_session.commit()

    retrieved = FileUpload.query.filter_by(city='Perth').first()
    assert retrieved is not None
    assert retrieved.filename == 'data.csv'
    assert retrieved.user.username == 'uploader'
