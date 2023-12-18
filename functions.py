from flask_bcrypt import bcrypt

class CarnetAdresse:
    def __init__(self):
        self.contacts = []

    def ajouter_contact(self, nom, prenom, email, numero):
        self.contacts.append({'nom': nom, 'prenom': prenom, 'email': email, 'numero': numero})

    def supprimer_contact(self, nom):
        self.contacts = [contact for contact in self.contacts if contact['nom'] != nom]

    def get_contact_par_id(self, contact_id):
        for contact in self.contacts:
            if contact['id'] == contact_id:
                return contact
        return None

    def modifier_contact(self, id_contact, nouveau_prenom, nouveau_nom, nouveau_email, nouveau_numero):
        for contact in self.contacts:
            if contact['id'] == id_contact:
                contact['nom'] = nouveau_nom
                contact['prenom'] = nouveau_prenom
                contact['email'] = nouveau_email
                contact['numero'] = nouveau_numero
                break

    def get_contacts(self):
        return self.contacts




def valid_login(password_hash, password):
    return bcrypt.check_password_hash(password_hash, password)