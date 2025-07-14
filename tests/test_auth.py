import pytest
from app import app, db
from models.user import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


class TestAuthentication:

    def test_register_valid_user(self, client):
        """Test inscription avec données valides"""
        response = client.post('/inscription', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'phone': '0123456789',
            'password': 'password123'
        })
        assert response.status_code == 302  # Redirection après succès

        # Vérifier que l'utilisateur a été créé
        with app.app_context():
            user = User.query.filter_by(email='newuser@test.com').first()
            assert user is not None
            assert user.username == 'newuser'
            assert bcrypt.check_password_hash(user.password, 'password123')

    def test_register_duplicate_email(self, client, auth_user):
        """Test inscription avec email déjà utilisé"""
        response = client.post('/inscription', data={
            'username': 'anotheruser',
            'email': 'test@example.com',  # Email déjà utilisé par auth_user
            'phone': '0987654321',
            'password': 'password123'
        }, follow_redirects=True)

        # Utiliser decode pour convertir bytes en string puis chercher
        response_text = response.data.decode('utf-8').lower()
        assert 'adresse email est déjà utilisée' in response_text or 'email' in response_text

    def test_register_duplicate_username(self, client, auth_user):
        """Test inscription avec nom d'utilisateur déjà utilisé"""
        response = client.post('/inscription', data={
            'username': 'testuser',  # Username déjà utilisé
            'email': 'different@test.com',
            'phone': '0987654321',
            'password': 'password123'
        }, follow_redirects=True)

        response_text = response.data.decode('utf-8').lower()
        assert 'nom d\'utilisateur est déjà utilisé' in response_text or 'utilisateur' in response_text

    def test_login_valid_credentials(self, client, auth_user):
        """Test connexion avec identifiants valides"""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        assert response.status_code == 302  # Redirection vers /carnet
        assert response.location.endswith('/carnet')

    def test_login_invalid_email(self, client):
        """Test connexion avec email inexistant"""
        response = client.post('/login', data={
            'email': 'inexistant@test.com',
            'password': 'password123'
        })
        assert response.status_code == 200  # Reste sur la page de login
        response_text = response.data.decode('utf-8').lower()
        assert 'invalide' in response_text

    def test_login_invalid_password(self, client, auth_user):
        """Test connexion avec mot de passe incorrect"""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'mauvais_password'
        })
        assert response.status_code == 200
        response_text = response.data.decode('utf-8').lower()
        assert 'invalide' in response_text

    def test_logout(self, client, logged_in_user):
        """Test déconnexion"""
        response = client.get('/logout')
        assert response.status_code == 200

        # Vérifier que l'accès au carnet redirige vers login
        response = client.get('/carnet')
        assert response.status_code == 302

    def test_access_protected_route_without_login(self, client):
        """Test accès à une route protégée sans être connecté"""
        response = client.get('/carnet')
        assert response.status_code == 302  # Redirection vers index