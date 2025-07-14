#!/usr/bin/env python3
"""
Script pour lancer les tests avec différentes options
"""
import subprocess
import sys
import os


def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n{'=' * 60}")
    print(f"🔄 {description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCÈS")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - ÉCHEC")
            print(f"Code de retour: {result.returncode}")
            if result.stderr:
                print("Erreurs:")
                print(result.stderr)
            if result.stdout:
                print("Sortie:")
                print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de: {command}")
        print(f"Exception: {e}")
        return False


def main():
    """Fonction principale"""
    print("🧪 Système de test pour Carnet d'Adresses")
    print("=" * 60)

    # Vérifier que les dépendances sont installées
    if not run_command("pip install -r requirements-test.txt", "Installation des dépendances de test"):
        print("❌ Impossible d'installer les dépendances. Arrêt.")
        sys.exit(1)

    # Menu interactif
    while True:
        print("\n" + "=" * 60)
        print("🎯 MENU DES TESTS")
        print("=" * 60)
        print("1. 🚀 Lancer TOUS les tests")
        print("2. 🔐 Tests d'authentification uniquement")
        print("3. 📝 Tests de validation des contacts")
        print("4. ⚙️  Tests de gestion des contacts")
        print("5. 🔒 Tests de sécurité")
        print("6. 🔗 Tests d'intégration")
        print("7. 📊 Tests avec rapport de couverture")
        print("8. 🐛 Tests en mode verbose")
        print("9. ⚡ Tests rapides (sans les lents)")
        print("0. ❌ Quitter")

        choice = input("\n👉 Votre choix (0-9): ").strip()

        if choice == "1":
            run_command("pytest tests/ -v", "Lancement de tous les tests")

        elif choice == "2":
            run_command("pytest tests/test_auth.py -v", "Tests d'authentification")

        elif choice == "3":
            run_command("pytest tests/test_contact_validation.py -v", "Tests de validation des contacts")

        elif choice == "4":
            run_command("pytest tests/test_contact_management.py -v", "Tests de gestion des contacts")

        elif choice == "5":
            run_command("pytest tests/test_security.py -v", "Tests de sécurité")

        elif choice == "6":
            run_command("pytest tests/test_integration.py -v", "Tests d'intégration")

        elif choice == "7":
            run_command("pytest tests/ --cov=app --cov=models --cov-report=html --cov-report=term",
                        "Tests avec rapport de couverture")
            print("\n📊 Rapport de couverture généré dans: htmlcov/index.html")

        elif choice == "8":
            run_command("pytest tests/ -v -s", "Tests en mode verbose")

        elif choice == "9":
            run_command("pytest tests/ -v -m 'not slow'", "Tests rapides")

        elif choice == "0":
            print("👋 Au revoir!")
            break

        else:
            print("❌ Choix invalide. Veuillez choisir entre 0 et 9.")


if __name__ == "__main__":
    main()