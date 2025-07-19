import pytest
from app import app, db, Contact


class TestContactManagement:

    def test_contact_crud_workflow(self, client, logged_in_user):
        """Test workflow CRUD complet sur les contacts"""

        # CREATE - Création contact
        response = client.post('/ajouter', data={
            'nom': 'Martin',
            'prenom': 'Pierre',
            'email': 'pierre.martin@email.com',
            'numero': '0198765432',
            'classe': 'professionnel'
        })
        assert response.status_code == 302

        with app.app_context():
            contact = Contact.query.filter_by(nom='Martin').first()
            assert contact is not None
            contact_id = contact.id

        # READ - Affichage dans la liste
        response = client.get('/carnet')
        assert b'Martin' in response.data
        assert b'Pierre' in response.data

        # UPDATE - Modification
        response = client.post(f'/modifier/{contact_id}', data={
            'nom': 'Martin',
            'prenom': 'Paul',  # Changement prénom
            'email': 'paul.martin@email.com',
            'numero': '0198765432',
            'classe': '2'  # professionnel
        })
        assert response.status_code == 302

        # Vérification modification
        with app.app_context():
            contact = Contact.query.get(contact_id)
            assert contact.prenom == 'Paul'
            assert contact.email == 'paul.martin@email.com'

        # DELETE - Suppression
        response = client.get(f'/supprimer/{contact_id}')
        assert response.status_code == 302

        # Vérification suppression
        with app.app_context():
            contact = Contact.query.get(contact_id)
            assert contact is None

    def test_search_functionality(self, client, logged_in_user):
        """Test fonctionnalité de recherche"""
        # Créer des contacts de test
        contacts_data = [
            ('Dupont', 'Jean', 'famille'),
            ('Martin', 'Paul', 'professionnel'),
            ('Durand', 'Marie', 'ami'),
            ('Dupuis', 'Luc', 'famille')
        ]

        for nom, prenom, classe in contacts_data:
            client.post('/ajouter', data={
                'nom': nom,
                'prenom': prenom,
                'email': f'{prenom.lower()}.{nom.lower()}@email.com',
                'numero': f'01234567{len(nom)}',
                'classe': classe
            })

        # Test recherche par nom partiel
        response = client.get('/rechercher?recherche=dup')
        assert b'Dupont' in response.data
        assert b'Dupuis' in response.data
        assert b'Martin' not in response.data

        # Test recherche par prénom
        response = client.get('/rechercher?recherche=jea')
        assert b'Jean' in response.data
        assert b'Paul' not in response.data

    def test_filter_functionality(self, client, logged_in_user):
        """Test fonctionnalités de filtrage"""
        # Créer des contacts de différentes catégories
        contacts_data = [
            ('Dupont', 'Jean', 'famille'),
            ('Martin', 'Paul', 'professionnel'),
            ('Durand', 'Marie', 'ami')
        ]

        for nom, prenom, classe in contacts_data:
            client.post('/ajouter', data={
                'nom': nom,
                'prenom': prenom,
                'email': f'{prenom.lower()}.{nom.lower()}@email.com',
                'numero': f'01234567{len(nom)}',
                'classe': classe
            })

        # Test filtrage par catégorie famille
        response = client.get('/filtrer/famille')
        assert b'Dupont' in response.data
        assert b'Martin' not in response.data
        assert b'Durand' not in response.data

        # Test filtrage par catégorie professionnel
        response = client.get('/filtrer/professionnel')
        assert b'Martin' in response.data
        assert b'Dupont' not in response.data

    def test_sort_functionality(self, client, logged_in_user):
        """Test fonctionnalités de tri"""
        # Créer des contacts
        contacts_data = [
            ('Zebra', 'Albert'),
            ('Alpha', 'Zoe'),
            ('Beta', 'Marie')
        ]

        for nom, prenom in contacts_data:
            client.post('/ajouter', data={
                'nom': nom,
                'prenom': prenom,
                'email': f'{prenom.lower()}.{nom.lower()}@email.com',
                'numero': f'01234567{len(nom)}',
                'classe': 'famille'
            })

        # Test tri par nom
        response = client.get('/trier/nom')
        content = response.data.decode('utf-8')
        alpha_pos = content.find('Alpha')
        beta_pos = content.find('Beta')
        zebra_pos = content.find('Zebra')

        assert alpha_pos < beta_pos < zebra_pos

        # Test tri par prénom
        response = client.get('/trier/prenom')
        content = response.data.decode('utf-8')
        albert_pos = content.find('Albert')
        marie_pos = content.find('Marie')
        zoe_pos = content.find('Zoe')

        assert albert_pos < marie_pos < zoe_pos