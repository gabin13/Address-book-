import pytest
from app import app, db, User, Contact
import io


class TestIntegration:

    def test_complete_user_journey(self, client):
        """Test parcours complet d'un nouvel utilisateur"""

        # 1. Accès page d'accueil
        response = client.get('/')
        assert response.status_code == 200
        assert 'Carnet d\'Adresses'.encode('utf-8') in response.data

        # 2. Inscription
        response = client.post('/inscription', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'phone': '0123456789',
            'password': 'NewUserPass123!'
        })
        assert response.status_code == 302

        # 3. Connexion
        response = client.post('/login', data={
            'email': 'newuser@test.com',
            'password': 'NewUserPass123!'
        })
        assert response.status_code == 302

        # 4. Accès carnet vide
        response = client.get('/carnet', follow_redirects=True)
        assert 'aucun contact'.encode('utf-8') in response.data.lower()

        # 5. Ajout premier contact
        response = client.post('/ajouter', data={
            'nom': 'Premier',
            'prenom': 'Contact',
            'email': 'premier@contact.com',
            'numero': '0111111111',
            'classe': 'famille'
        })

        # 6. Vérification affichage
        response = client.get('/carnet')
        assert b'Premier' in response.data
        assert b'Contact' in response.data

        # 7. Export des contacts
        response = client.get('/exporter_contacts')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

        # 8. Déconnexion
        response = client.get('/logout')
        assert response.status_code == 302  # Redirection après logout

        # 9. Vérification perte d'accès
        response = client.get('/carnet')
        assert response.status_code == 302  # Redirection vers index

    def test_multi_user_data_isolation(self, client):
        """Test isolation données entre utilisateurs multiples"""

        # Création de deux utilisateurs
        users_data = [
            ('user1', 'user1@test.com', 'pass1'),
            ('user2', 'user2@test.com', 'pass2')
        ]

        for username, email, password in users_data:
            client.post('/inscription', data={
                'username': username,
                'email': email,
                'phone': f'01{username[-1] * 8}',
                'password': password
            })

        # User1 ajoute des contacts
        client.post('/login', data={'email': 'user1@test.com', 'password': 'pass1'})
        client.post('/ajouter', data={
            'nom': 'ContactUser1',
            'prenom': 'Test',
            'email': 'test1@email.com',
            'numero': '0111111111',
            'classe': 'famille'
        })
        client.get('/logout')

        # User2 se connecte et vérifie isolation
        client.post('/login', data={'email': 'user2@test.com', 'password': 'pass2'})
        response = client.get('/carnet')
        assert b'ContactUser1' not in response.data

        # User2 ajoute son contact
        client.post('/ajouter', data={
            'nom': 'ContactUser2',
            'prenom': 'Test',
            'email': 'test2@email.com',
            'numero': '0222222222',
            'classe': 'ami'
        })

        # Vérifier que chaque utilisateur ne voit que ses contacts
        response = client.get('/carnet')
        assert b'ContactUser2' in response.data
        assert b'ContactUser1' not in response.data

    def test_csv_import_export_workflow(self, client, logged_in_user):
        """Test workflow complet import/export CSV"""

        # Créer quelques contacts
        contacts_data = [
            ('Dupont', 'Jean', 'jean@email.com', '0123456789', 'famille'),
            ('Martin', 'Marie', 'marie@email.com', '0198765432', 'professionnel')
        ]

        for nom, prenom, email, numero, classe in contacts_data:
            client.post('/ajouter', data={
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'numero': numero,
                'classe': classe
            })

        # Export CSV
        response = client.get('/exporter_contacts')
        assert response.status_code == 200
        csv_content = response.data.decode('utf-8')

        # Vérifier le contenu du CSV
        assert 'Dupont,Jean' in csv_content
        assert 'Martin,Marie' in csv_content

        # Supprimer tous les contacts pour tester l'import
        with app.app_context():
            Contact.query.filter_by(user_id=logged_in_user.id).delete()
            db.session.commit()

        # Préparer un fichier CSV pour l'import
        csv_data = """Nom,Prénom,Email,Numéro,Classe
Nouveau,Contact,nouveau@test.com,0111111111,ami
Autre,Personne,autre@test.com,0222222222,famille"""

        # Import CSV
        data = {
            'fichier_csv': (io.BytesIO(csv_data.encode()), 'test.csv')
        }
        response = client.post('/importer_contacts',
                               data=data,
                               content_type='multipart/form-data')

        # Vérifier que les contacts ont été importés
        response = client.get('/carnet')
        assert b'Nouveau' in response.data
        assert b'Autre' in response.data

    def test_search_and_filter_integration(self, client, logged_in_user):
        """Test intégration recherche et filtres"""

        # Créer des contacts variés
        contacts_data = [
            ('Dupont', 'Jean', 'famille'),
            ('Durand', 'Marie', 'ami'),
            ('Martin', 'Paul', 'professionnel'),
            ('Dupuis', 'Luc', 'famille'),
            ('Dubois', 'Anne', 'professionnel')
        ]

        for nom, prenom, classe in contacts_data:
            client.post('/ajouter', data={
                'nom': nom,
                'prenom': prenom,
                'email': f'{prenom.lower()}.{nom.lower()}@email.com',
                'numero': f'01234567{len(nom)}',
                'classe': classe
            })

        # Test recherche avec terme partiel
        response = client.get('/rechercher?recherche=du')
        content = response.data.decode('utf-8')
        assert 'Dupont' in content
        assert 'Durand' in content
        assert 'Dupuis' in content
        assert 'Dubois' in content
        assert 'Martin' not in content

        # Test filtrage par catégorie
        response = client.get('/filtrer/famille')
        content = response.data.decode('utf-8')
        assert 'Dupont' in content
        assert 'Dupuis' in content
        assert 'Martin' not in content
        assert 'Durand' not in content

        # Test tri par nom
        response = client.get('/trier/nom')
        content = response.data.decode('utf-8')

        # Vérifier l'ordre alphabétique
        positions = {}
        for nom in ['Dubois', 'Dupont', 'Dupuis', 'Durand', 'Martin']:
            positions[nom] = content.find(nom)

        # Dubois devrait venir avant Dupont, etc.
        assert positions['Dubois'] < positions['Dupont']
        assert positions['Dupont'] < positions['Dupuis']
        assert positions['Dupuis'] < positions['Durand']
        assert positions['Durand'] < positions['Martin']

    def test_contact_modification_workflow(self, client, logged_in_user):
        """Test workflow complet de modification de contact"""

        # Créer un contact
        response = client.post('/ajouter', data={
            'nom': 'Original',
            'prenom': 'Contact',
            'email': 'original@email.com',
            'numero': '0123456789',
            'classe': 'famille'
        })

        # Récupérer l'ID du contact créé
        with app.app_context():
            contact = Contact.query.filter_by(nom='Original').first()
            contact_id = contact.id

        # Accéder au formulaire de modification
        response = client.get(f'/modifier/{contact_id}')
        assert response.status_code == 200
        assert b'Original' in response.data
        assert b'Contact' in response.data

        # Modifier le contact
        response = client.post(f'/modifier/{contact_id}', data={
            'nom': 'Modifie',
            'prenom': 'ContactMod',
            'email': 'modifie@email.com',
            'numero': '0987654321',
            'classe': '2'  # professionnel
        })
        assert response.status_code == 302

        # Vérifier les modifications
        response = client.get('/carnet')
        assert b'Modifie' in response.data
        assert b'ContactMod' in response.data
        assert b'modifie@email.com' in response.data
        assert b'0987654321' in response.data
        assert b'Original' not in response.data

        # Vérifier en base de données
        with app.app_context():
            contact = Contact.query.get(contact_id)
            assert contact.nom == 'Modifie'
            assert contact.prenom == 'ContactMod'
            assert contact.email == 'modifie@email.com'
            assert contact.numero == '0987654321'
            assert contact.classe_id == 2

    def test_account_deletion_workflow(self, client):
        """Test workflow complet de suppression de compte"""

        # Créer un utilisateur
        client.post('/inscription', data={
            'username': 'userdelete',
            'email': 'delete@test.com',
            'phone': '0123456789',
            'password': 'password123'
        })

        # Se connecter
        client.post('/login', data={
            'email': 'delete@test.com',
            'password': 'password123'
        })

        # Ajouter des contacts
        for i in range(3):
            client.post('/ajouter', data={
                'nom': f'Contact{i}',
                'prenom': f'Test{i}',
                'email': f'test{i}@email.com',
                'numero': f'012345678{i}',
                'classe': 'famille'
            })

        # Vérifier que les contacts existent
        with app.app_context():
            user = User.query.filter_by(email='delete@test.com').first()
            contacts_count = Contact.query.filter_by(user_id=user.id).count()
            assert contacts_count == 3

        # Supprimer le compte
        response = client.post('/supprimer_compte')
        assert response.status_code == 302

        # Vérifier que l'utilisateur et ses contacts ont été supprimés
        with app.app_context():
            user = User.query.filter_by(email='delete@test.com').first()
            assert user is None

            # Vérifier qu'aucun contact orphelin ne reste
            orphan_contacts = Contact.query.filter_by(user_id=user.id if user else -1).count()
            assert orphan_contacts == 0