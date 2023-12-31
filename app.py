from flask import Flask, render_template, request, redirect, url_for, flash, Response, make_response, session
from functions import CarnetAdresse
from pprint import pprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import desc, asc
from io import StringIO
from flask_bcrypt import Bcrypt
from flask import request, jsonify
from datetime import datetime
import csv

app = Flask(__name__)
carnet = CarnetAdresse()
app.secret_key = "b'_5#y2LF4Q8z\n\xec]/'"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:_root453*@localhost:3306/hackathon'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


from models.user import User


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
class Classe(db.Model):
    __tablename__ = 'classe'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)

    contacts = db.relationship('Contact', backref='classe', lazy=True)

class Contact(db.Model):
    __tablename__ = 'contact'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    numero = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    classe_id = db.Column(db.Integer, db.ForeignKey('classe.id'))  # Colonne pour stocker la classe choisie
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


#Activation du mode sombre

@app.route('/activer_mode_sombre')
def activer_mode_sombre():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('mode_sombre', 'true')
    return response

@app.route('/desactiver_mode_sombre')
def desactiver_mode_sombre():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('mode_sombre', '', expires=0)
    return response


#Affichage des cartes

@app.route('/activer_affichage_cartes')
def activer_affichage_cartes():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('affichage_cartes', 'true')
    return response

@app.route('/desactiver_affichage_cartes')
def desactiver_affichage_cartes():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('affichage_cartes', '', expires=0)
    return response


@app.get("/")
def index():
    return render_template('index.html')



#user

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None

    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            session['username'] = request.form['username']
            session['user_id'] = user.id
            return redirect(url_for('carnet'))
        else:
            error = 'Invalid username/password'

    return render_template('auth/login.html', error=error)



@app.get('/register')
def register():
    return render_template('auth/register.html')

@app.post('/inscription')
def inscription():
    username = request.form['username']
    password = request.form['password']

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Ce nom d\'utilisateur est déjà utilisé.', 'custom-style')
        return redirect(url_for('register'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.get('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)

    return render_template('index.html')




#contact

@app.route('/carnet')
def carnet():
    mode_sombre_active = request.cookies.get('mode_sombre') == 'true'
    user_id = session.get('user_id')

    if user_id is None:
        flash('Vous devez être connecté pour accéder au carnet d\'adresses.', 'custom-style')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    username = user.username if user else "Utilisateur inconnu"

    contacts = Contact.query.filter_by(user_id=user_id).all()

    affichage_cartes = request.cookies.get('affichage_cartes') == 'true'

    return render_template('carnet.html', username=username, contacts=contacts, mode_sombre_active=mode_sombre_active, affichage_cartes=affichage_cartes)

@app.get('/ajout')
def ajout():
    mode_sombre_active = request.cookies.get('mode_sombre') == 'true'

    user_id = session.get('user_id')
    if user_id is None:
        flash('Vous devez être connecté pour accéder à cette page.', 'custom-style')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    username = user.username if user else "Utilisateur inconnu"

    classes = [
        {'id': 1, 'nom': 'famille'},
        {'id': 2, 'nom': 'professionnel'},
        {'id': 3, 'nom': 'ami'}
    ]

    affichage_cartes = request.cookies.get('affichage_cartes') == 'true'
    return render_template('add.html', username=username, classes=classes, mode_sombre_active=mode_sombre_active, affichage_cartes=affichage_cartes)


@app.route('/ajouter', methods=['POST'])
def ajouter():
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    numero = request.form['numero']
    classe_nom = request.form['classe']

    user_id = session.get('user_id')

    if user_id:
        existing_contact = Contact.query.filter_by(nom=nom, prenom=prenom, user_id=user_id).first()

        if existing_contact:
            flash('Ce contact existe déjà.', 'custom-style')
            return redirect(url_for('carnet'))

        classe = Classe.query.filter_by(nom=classe_nom).first()

        if classe:
            classe_id = classe.id
            nouveau_contact = Contact(
                nom=nom,
                prenom=prenom,
                email=email,
                numero=numero,
                user_id=user_id,
                classe_id=classe_id
            )

            db.session.add(nouveau_contact)
            db.session.commit()

            flash('Contact ajouté avec succès', 'success')
            return redirect(url_for('carnet'))
        else:
            flash('Classe invalide', 'danger')
            return redirect(url_for('carnet'))
    else:
        flash('Utilisateur non connecté', 'danger')
        return redirect(url_for('login'))




@app.route('/supprimer/<int:id_contact>', methods=['GET'])
def supprimer(id_contact):
    contact_a_supprimer = Contact.query.get_or_404(id_contact)
    db.session.delete(contact_a_supprimer)
    db.session.commit()
    return redirect(url_for('carnet'))


@app.route('/modifier/<int:id_contact>', methods=['GET'])
def afficher_formulaire_modification(id_contact):
    mode_sombre_active = request.cookies.get('mode_sombre') == 'true'

    user_id = session.get('user_id')
    if user_id is None:
        flash('Vous devez être connecté pour accéder à cette page.', 'custom-style')
        return redirect(url_for('index'))

    contact = Contact.query.get_or_404(id_contact)
    user = User.query.get(user_id)
    username = user.username if user else "Utilisateur inconnu"

    classes = [
        {'id': 1, 'nom': 'Famille'},
        {'id': 2, 'nom': 'Professionnel'},
        {'id': 3, 'nom': 'Ami'}
    ]

    affichage_cartes = request.cookies.get('affichage_cartes') == 'true'
    return render_template('edit.html', contact=contact, username=username, classes=classes, mode_sombre_active=mode_sombre_active, affichage_cartes=affichage_cartes)



@app.route('/modifier/<int:id_contact>', methods=['POST'])
def modifier_contact(id_contact):
    contact_a_modifier = Contact.query.get_or_404(id_contact)

    contact_a_modifier.nom = request.form['nom']
    contact_a_modifier.prenom = request.form['prenom']
    contact_a_modifier.email = request.form['email']
    contact_a_modifier.numero = request.form['numero']
    contact_a_modifier.classe_id = request.form['classe']

    db.session.commit()

    return redirect(url_for('carnet'))


@app.route('/rechercher', methods=['GET'])
def rechercher():
    mode_sombre_active = request.cookies.get('mode_sombre') == 'true'
    terme_recherche = request.args.get('recherche', '').lower()

    user_id = session.get('user_id')

    if user_id is None:
        flash('Vous devez être connecté pour effectuer une recherche.', 'custom-style')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    username = user.username if user else "Utilisateur inconnu"

    resultats_recherche = Contact.query.filter(
        (Contact.user_id == user_id) &
        ((func.lower(Contact.nom).startswith(terme_recherche)) |
         (func.lower(Contact.prenom).startswith(terme_recherche)))
    ).all()

    affichage_cartes = request.cookies.get('affichage_cartes') == 'true'
    return render_template('recherche.html', resultats=resultats_recherche, username=username, mode_sombre_active=mode_sombre_active, affichage_cartes=affichage_cartes)



@app.route('/trier/<critere>', methods=['GET'])
def trier_contacts(critere):
    mode_sombre_active = request.cookies.get('mode_sombre') == 'true'
    user_id = session.get('user_id')

    if critere == 'prenom':
        contacts = Contact.query.filter(Contact.user_id == user_id).order_by(Contact.prenom).all()
    elif critere == 'nom':
        contacts = Contact.query.filter(Contact.user_id == user_id).order_by(Contact.nom).all()
    elif critere == 'ajout_decroi':
        contacts = Contact.query.filter(Contact.user_id == user_id).order_by(desc(Contact.created_at)).all()
    elif critere == 'ajout_croi':
        contacts = Contact.query.filter(Contact.user_id == user_id).order_by(asc(Contact.created_at)).all()
    else:
        flash('Critère de tri invalide', 'custom-style')
        return redirect(url_for('carnet'))

    user = User.query.get(user_id)
    username = user.username if user else "Utilisateur inconnu"

    affichage_cartes = request.cookies.get('affichage_cartes') == 'true'
    return render_template('carnet.html', contacts=contacts, mode_sombre_active=mode_sombre_active, username=username, affichage_cartes=affichage_cartes)


@app.route('/filtrer/<string:critere>', methods=['GET'])
def filtrer_contacts(critere):
    mode_sombre_active = request.cookies.get('mode_sombre') == 'true'
    user_id = session.get('user_id')
    prev_url = request.referrer
    contacts = []

    if critere == 'aucun':
        contacts = Contact.query.filter(Contact.user_id == user_id).all()
    elif critere == 'famille':
        contacts = Contact.query.filter(Contact.user_id == user_id, Contact.classe_id == 1).order_by(Contact.prenom).all()
    elif critere == 'professionnel':
        contacts = Contact.query.filter(Contact.user_id == user_id, Contact.classe_id == 2).order_by(Contact.nom).all()
    elif critere == 'ami':
        contacts = Contact.query.filter(Contact.user_id == user_id, Contact.classe_id == 3).order_by(desc(Contact.created_at)).all()
    else:
        flash('Critère de filtrage invalide', 'custom-style')
        return redirect(request.referrer)

    user = User.query.get(user_id)
    username = user.username if user else "Utilisateur inconnu"

    affichage_cartes = request.cookies.get('affichage_cartes') == 'true'
    return render_template('carnet.html', contacts=contacts, mode_sombre_active=mode_sombre_active, username=username, affichage_cartes=affichage_cartes)


@app.route('/exporter_contacts')
def exporter_contacts():
    contacts = Contact.query.all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Nom', 'Prénom', 'Email', 'Numéro'])

    for contact in contacts:
        writer.writerow([contact.nom, contact.prenom, contact.email, contact.numero])

    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=contacts.csv"})


@app.route('/importer_contacts', methods=['POST'])
def importer_contacts():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Vous devez être connecté pour importer des contacts.', 'error')
        return redirect(url_for('carnet'))

    if 'fichier_csv' not in request.files:
        flash('Aucun fichier CSV n\'a été envoyé.', 'custom-style')
        return redirect(url_for('carnet'))

    fichier = request.files['fichier_csv']

    if fichier.filename == '':
        flash('Aucun fichier sélectionné.', 'custom-style')
        return redirect(url_for('carnet'))

    if fichier:
        lignes = fichier.stream.read().decode("UTF8").splitlines()
        lecteur = csv.reader(lignes, delimiter=',')
        next(lecteur, None)

        for ligne in lecteur:
            contact_existant = Contact.query.filter_by(
                nom=ligne[0],
                prenom=ligne[1],
                user_id=user_id
            ).first()

            if not contact_existant:
                nouveau_contact = Contact(
                    nom=ligne[0],
                    prenom=ligne[1],
                    email=ligne[2],
                    numero=ligne[3],
                    user_id=user_id
                )
                db.session.add(nouveau_contact)

        db.session.commit()
        flash('Importation des contacts réussie.', 'success')
        return redirect(url_for('carnet'))
    else:
        flash('Échec de l\'importation des contacts.', 'custom-style')
        return redirect(url_for('carnet'))

@app.route('/supprimer_compte', methods=['POST'])
def supprimer_compte():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Vous devez être connecté pour supprimer votre compte.', 'error')
        return redirect(url_for('login'))

    contacts_a_supprimer = Contact.query.filter_by(user_id=user_id).all()
    for contact in contacts_a_supprimer:
        db.session.delete(contact)

    user_a_supprimer = User.query.get(user_id)
    if user_a_supprimer:
        db.session.delete(user_a_supprimer)
        db.session.commit()
        session.clear()
        flash('Votre compte et tous les contacts ont été supprimés avec succès.', 'success')
        return redirect(url_for('index'))
    else:
        flash('Utilisateur non trouvé.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
