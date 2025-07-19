import pytest
from app import app, db, User, Contact
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


class TestSecurity:

    def test_password_hashing(self):
        """Test hachage sécurisé des mots de passe"""
        password = "motdepasse123"
        hash1 = bcrypt.generate_password_hash(password)
        hash2 = bcrypt.generate_password_hash(password)

        # Deux hachages du même mot de passe sont différents (salt)
        assert hash1 != hash2

        # Vérification du mot de passe
        assert bcrypt.check_password_hash(hash1, password)
        assert bcrypt.check_password_hash(hash2, password)
        assert not bcrypt.check_password_hash(hash1, "mauvais_password")

    def test_session_management(self, client):
        """Test gestion des sessions utilisateur"""
        # Test accès non autorisé
        response = client.get('/carnet')
        assert response.status_code == 302  # Redirection vers index

        # Test après connexion
        with app.app_context():
            password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
            user = User(
                username='testuser',
                email='test@email.com',
                phone='0123456789',
                password=password_hash
            )
            db.session.add(user)
            db.session.commit()

            with client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['username'] = user.username

            response = client.get('/carnet')
            assert response.status_code == 200

    def test_user_data_isolation(self, client):
        """Test isolation des données entre utilisateurs"""
        with app.app_context():
            # Création de deux utilisateurs
            user1 = User(username='user1', email='user1@email.com',
                         phone='0111111111', password='hash1')
            user2 = User(username='user2', email='user2@email.com',
                         phone='0222222222', password='hash2')
            db.session.add_all([user1, user2])
            db.session.commit()

            # Contact pour user1
            contact1 = Contact(nom='Contact1', prenom='User1',
                               email='contact1@email.com', numero='0111111111',
                               user_id=user1.id, classe_id=1)
            db.session.add(contact1)
            db.session.commit()

            # Vérification que user2 ne voit pas le contact de user1
            with client.session_transaction() as sess:
                sess['user_id'] = user2.id

            response = client.get('/carnet')
            assert b'Contact1' not in response.data

    def test_sql_injection_protection(self, client, logged_in_user):
        """Test protection contre l'injection SQL"""
        # Tentative d'injection SQL dans la recherche
        malicious_input = "'; DROP TABLE contact; --"
        response = client.get(f'/rechercher?recherche={malicious_input}')

        # La requête ne devrait pas planter
        assert response.status_code == 200

        # Vérifier que la table existe toujours
        with app.app_context():
            contacts = Contact.query.all()
            # La requête devrait fonctionner normalement

    def test_xss_protection(self, client, logged_in_user):
        """Test protection contre XSS"""
        # Tentative d'injection de script
        malicious_script = "<script>alert('XSS')</script>"

        response = client.post('/ajouter', data={
            'nom': malicious_script,
            'prenom': 'Test',
            'email': 'test@email.com',
            'numero': '0123456789',
            'classe': 'famille'
        })

        # Vérifier que le script n'est pas exécuté dans la page
        response = client.get('/carnet')
        # Le script devrait être échappé ou nettoyé
        assert b'<script>' not in response.data
        assert b'&lt;script&gt;' in response.data or malicious_script.encode() not in response.data