
# Approche alternative pour les assertions avec texte français
# Au lieu de: assert b'texte français' in response.data
# Utiliser: assert 'texte français' in response.data.decode('utf-8')

def check_french_text_in_response(response, expected_text):
    """Helper function pour vérifier du texte français dans une réponse"""
    return expected_text.lower() in response.data.decode('utf-8').lower()

# Exemple d'utilisation:
# assert check_french_text_in_response(response, 'contact existe déjà')
