import pytest
import os
import sys
import tempfile

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch temporaire pour Werkzeug si nécessaire
try:
    import werkzeug

    if not hasattr(werkzeug, '__version__'):
        # Essayer de récupérer la version autrement
        try:
            import pkg_resources

            werkzeug.__version__ = pkg_resources.get_distribution('werkzeug').version
        except:
            # Version par défaut si tout échoue
            werkzeug.__version__ = '2.3.7'
except:
    pass

from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


@pytest.fixture(scope='function')
def client():
    """Créer un client de test simple"""
    # Import tardif pour éviter les problèmes circulaires
    from app import app, db, Classe

    # Sauvegarder la config originale
    original_config = app.config.copy()

    try:
        # Configuration pour les tests
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        })

        # Créer le client de test
        test_client = app.test_client()

        # Setup de la base de données
        with app.app_context():
            db.create_all()

            # NOUVEAU : Créer les classes par défaut
            classes_default = [
                {'id': 1, 'nom': 'famille'},
                {'id': 2, 'nom': 'professionnel'},
                {'id': 3, 'nom': 'ami'}
            ]

            for classe_data in classes_default:
                existing_classe = Classe.query.filter_by(id=classe_data['id']).first()
                if not existing_classe:
                    classe = Classe(id=classe_data['id'], nom=classe_data['nom'])
                    db.session.add(classe)

            db.session.commit()
            print("✅ Base de données initialisée avec succès")

        yield test_client

        # Cleanup
        with app.app_context():
            db.session.remove()
            db.drop_all()

    finally:
        # Restaurer la config originale
        app.config.update(original_config)


@pytest.fixture
def auth_user(client):
    """Crée un utilisateur de test authentifié"""
    from app import app, db, User

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

        # Refresh pour obtenir l'ID
        db.session.refresh(user)
        return user


@pytest.fixture
def logged_in_user(client, auth_user):
    """Simule un utilisateur connecté"""
    with client.session_transaction() as sess:
        sess['user_id'] = auth_user.id
        sess['username'] = auth_user.username
    return auth_user


@pytest.fixture
def sample_contact(client, auth_user):
    """Crée un contact de test"""
    from app import app, db, Contact

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

        db.session.refresh(contact)
        return contact