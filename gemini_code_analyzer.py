
import os
import sys
import subprocess
from google import genai
from google.genai.errors import APIError
# Importation de la nouvelle bibliothèque
from dotenv import load_dotenv # <-- Nouvelle importation

# --- Configuration ---
MODEL_NAME = 'gemini-2.5-flash' 
# ... (Les fonctions get_staged_files() et analyze_code_with_gemini() restent inchangées) ...

def main():
    
    # 1. Chargement de la clé API à partir de .env
    # Cette fonction cherche le fichier .env et charge les variables
    # dans les variables d'environnement du processus Python.
    load_dotenv()
    
    # 2. Vérification de la clé API
    # Maintenant, os.getenv("GEMINI_API_KEY") lira la valeur du .env
    if not os.getenv("GEMINI_API_KEY"):
        print("\n🛑 ERREUR CRITIQUE: La variable d'environnement GEMINI_API_KEY n'est pas définie.", file=sys.stderr)
        print("Veuillez créer un fichier .env à la racine du projet avec GEMINI_API_KEY='VOTRE_CLÉ' et vous assurer qu'elle est correcte.", file=sys.stderr)
        # Quitter avec un code d'erreur (1) si la clé est manquante
        sys.exit(1)

    print("--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---")
    
    # ... (Reste de la fonction main() inchangé) ...
    # Le reste du script fonctionnera car la clé est maintenant chargée.
    
    # ...