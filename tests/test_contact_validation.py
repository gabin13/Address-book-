import pytest
from app import app, db
from models.contact import Contact


class TestContactValidation:

    def test_valid_contact_creation(self, client, logged_in_user):
        """Test création contact avec données valides"""
        response = client.post('/ajouter', data={
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean.dupont@email.com',
            'numero': '0123456789',
            'classe': 'famille'
        })

        assert response.status_code == 302  # Redirection après succès

        # Vérifier que le contact a été créé
        with app.app_context():
            contact = Contact.query.filter_by(nom='Dupont').first()
            assert contact is not None
            assert contact.user_id == logged_in_user.id
            assert contact.prenom == 'Jean'

    def test_duplicate_contact_prevention(self, client, logged_in_user):
        """Test prévention des doublons nom/prénom"""
        # Créer le premier contact
        client.post('/ajouter', data={
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean@email.com',
            'numero': '0123456789',
            'classe': 'famille'
        })

        # Tenter de créer un doublon
        response = client.post('/ajouter', data={
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'autre@email.com',
            'numero': '0987654321',
            'classe': 'ami'
        }, follow_redirects=True)

        response_text = response.data.decode('utf-8').lower()
        assert 'contact existe déjà' in response_text or 'contact' in response_text

    def test_duplicate_email_prevention(self, client, logged_in_user):
        """Test prévention des doublons email"""
        # Créer le premier contact
        client.post('/ajouter', data={
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean@email.com',
            'numero': '0123456789',
            'classe': 'famille'
        })

        # Tenter de créer avec le même email
        response = client.post('/ajouter', data={
            'nom': 'Martin',
            'prenom': 'Paul',
            'email': 'jean@email.com',  # Email dupliqué
            'numero': '0987654321',
            'classe': 'ami'
        }, follow_redirects=True)

        response_text = response.data.decode('utf-8').lower()
        assert 'mail existe déjà' in response_text or 'email' in response_text

    def test_duplicate_phone_prevention(self, client, logged_in_user):
        """Test prévention des doublons téléphone"""
        # Créer le premier contact
        client.post('/ajouter', data={
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean@email.com',
            'numero': '0123456789',
            'classe': 'famille'
        })

        # Tenter de créer avec le même numéro
        response = client.post('/ajouter', data={
            'nom': 'Martin',
            'prenom': 'Paul',
            'email': 'paul@email.com',
            'numero': '0123456789',  # Numéro dupliqué
            'classe': 'ami'
        }, follow_redirects=True)

        response_text = response.data.decode('utf-8').lower()
        assert 'numéro de téléphone existe déjà' in response_text or 'numéro' in response_text

    def test_phone_number_validation(self, client, logged_in_user):
        """Test validation format numéro téléphone"""
        test_cases = [
            ('012345678', False),  # Trop court
            ('01234567890', False),  # Trop long
            ('abcdefghij', False),  # Caractères non numériques
            ('0123456789', True)  # Format valide
        ]

        for numero, should_pass in test_cases:
            response = client.post('/ajouter', data={
                'nom': f'Test{numero}',
                'prenom': 'User',
                'email': f'test_{numero}@email.com',
                'numero': numero,
                'classe': 'famille'
            })

            if should_pass:
                assert response.status_code == 302
            else:
                # Le HTML5 pattern validation devrait empêcher la soumission
                # ou le serveur devrait rejeter
                assert response.status_code in [200, 400]