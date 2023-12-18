function confirmDelete(contactId) {
    var confirmation = confirm("Êtes-vous sûr de vouloir supprimer ce contact ?");
    if (confirmation) {
        window.location.href = '/supprimer/' + contactId;
    }
}

function exportContacts() {
    window.location.href = '/exporter_contacts';
}

function activerModeSombre() {
    fetch('/activer_mode_sombre', { method: 'GET' })
        .then(() => {
            document.body.classList.add('mode-sombre');
            document.cookie = 'mode_sombre=true; path=/';
        })
        .catch(error => console.error('Erreur : ', error));
}

function desactiverModeSombre() {
    fetch('/desactiver_mode_sombre', { method: 'GET' })
        .then(() => {
            document.body.classList.remove('mode-sombre');
            document.cookie = 'mode_sombre=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        })
        .catch(error => console.error('Erreur : ', error));
}


const affichageListe = document.querySelector('#affichageListe');
const affichageCartes = document.querySelector('#affichageCartes');


const listeContacts = document.querySelector('#contactsList');
const cartesContacts = document.querySelector('#contactsCards');


function afficherListe() {
    listeContacts.style.display = 'block';
    cartesContacts.style.display = 'none';
}


function afficherCartes() {
    listeContacts.style.display = 'none';
    cartesContacts.style.display = 'block';
}


affichageListe.addEventListener('click', afficherListe);
affichageCartes.addEventListener('click', afficherCartes);


document.getElementById('form-supprimer-compte').addEventListener('submit', function(event) {
    event.preventDefault(); // Empêche la soumission du formulaire par défaut

    if (confirm("Voulez-vous vraiment supprimer ce compte et tous les contacts associés ?")) {
        this.submit(); // Soumission du formulaire si la confirmation est acceptée
    }
});
