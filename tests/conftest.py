import pytest
import tempfile
import os
from app import app, db
from models.user import User
from models.contact import Contact
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


@pytest.fixture
def client():
    """Configure le client de test avec une base de données en mémoire"""
    # Créer un fichier temporaire pour la DB de test
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
def auth_user(client):
    """Crée un utilisateur de test authentifié"""
    with app.app_context():
        password_hash = bcrypt.generate_password_hash('password123').decode('utf-8')
        user = User(
            username='testuser',
            email='test@example.com',
            phone='0123456789',
            password=password_hash
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def logged_in_user(client, auth_user):
    """Simule un utilisateur connecté"""
    with client.session_transaction() as sess:
        sess['user_id'] = auth_user.id
        sess['username'] = auth_user.username
    return auth_user


@pytest.fixture
def sample_contact(auth_user):
    """Crée un contact de test"""
    with app.app_context():
        contact = Contact(
            nom='Dupont',
            prenom='Jean',
            email='jean.dupont@email.com',
            numero='0123456789',
            user_id=auth_user.id,
            classe_id=1
        )
        db.session.add(contact)
        db.session.commit()
        return contact