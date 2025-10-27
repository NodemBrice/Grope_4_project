# gemini_code_analyzer.py

import os
import sys
import subprocess
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

# --- Configuration ---
MODEL_NAME = 'gemini-2.5-flash'

def get_staged_files():
    """Récupère la liste de TOUS les fichiers modifiés entre la branche locale (HEAD) 
    et la dernière version distante connue (origin/main), ce qui correspond aux commits à pousser.
    """
    try:
        # La commande la plus fiable pour un pre-push : compare la HEAD locale avec l'état distant
        # '...' assure que la comparaison inclut tous les commits entre les deux références.
        command = ["git", "diff", "--name-only", "origin/main...HEAD"]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
        
        # Filtre les fichiers non pertinents
        files = [f for f in files if f and not f.endswith(('.png', '.jpg', '.lock', '.min.js', '.map', '.log', '.md', '.env', '.gitignore'))]
        
        # Point de contrôle DEBUG:
        print(f"DEBUG: Fichiers détectés par Git pour l'analyse: {files}", file=sys.stderr) 
        
        return files
        
    except subprocess.CalledProcessError as e:
        # Ceci peut arriver si origin/main n'est pas encore traqué.
        print(f"Avertissement (Git Error): Impossible de comparer avec origin/main. Erreur: {e.stderr.strip()}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Avertissement (Detection Error): {e}", file=sys.stderr)
        return []

def analyze_code_with_gemini(file_path):
    """DOIT ÊTRE PRÉSENTE : Gère l'appel à l'API Gemini."""
    # (Le corps de cette fonction doit appeler genai.Client() et générer le contenu)
    # ... code de la fonction ...
    return "OK" # TEMPORAIRE

def main():
    # ... (Votre code pour le chargement et la vérification de la clé) ...
    # ...

    print("--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---")

    # B. Logique Manquante (Début de main)
    files_to_check = get_staged_files()
    
    # 1. Sortie explicite si rien à analyser (important pour éviter le silence)
    if not files_to_check:
        print("\n--- INFO HOOK : Aucun fichier de code pertinent trouvé pour l'analyse Gemini. Poursuite du push. ---")
        sys.exit(0)
    
    problem_found = False
    
    # 2. Boucle d'Analyse Manquante
    for file_path in files_to_check:
        result = analyze_code_with_gemini(file_path)
        # ... Logique pour vérifier la réponse de Gemini et mettre problem_found à True ...
    
    # C. Logique Manquante (Fin de main)
    if problem_found:
        print("\n!!! 🛑 PUSH ANNULÉ : Des problèmes de code critiques ont été détectés. !!!")
        sys.exit(1) # Bloque le push
    else:
        print("\n--- ✅ Analyse terminée. Code propre. Poursuite du push. ---")
        sys.exit(0) # Permet le push

if __name__ == "__main__":
    main()
