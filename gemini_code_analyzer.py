# gemini_code_analyzer.py

import os
import sys
import subprocess
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

# --- Configuration ---
MODEL_NAME = 'gemini-2.5-flash' # Modèle rapide et performant pour l'analyse de code

def get_staged_files():
    """
    Récupère la liste de TOUS les fichiers modifiés entre la branche locale (HEAD) 
    et la dernière version distante connue (origin/main), ce qui correspond aux commits à pousser.
    """
    try:
        # Utiliser 'origin/main...HEAD' pour comparer tous les commits à pousser.
        command = ["git", "diff", "--name-only", "origin/main...HEAD"]
        
        # Le hook pre-push doit ignorer la sortie standard pour ne pas la polluer
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
        
        # Filtre les fichiers non pertinents (comme les images, les logs, les fichiers de configuration)
        files_to_check = [
            f for f in files 
            if f and not f.endswith(('.png', '.jpg', '.lock', '.min.js', '.map', '.log', '.md', '.env', '.gitignore', '.csv', '.json'))
        ]
        
        # DEBUG: Affiche les fichiers détectés sur la sortie d'erreur standard (stderr) pour qu'elle ne soit pas confondue avec l'output de l'IA
        print(f"DEBUG: Fichiers détectés par Git pour l'analyse: {files_to_check}", file=sys.stderr) 
        
        return files_to_check
        
    except subprocess.CalledProcessError as e:
        # Se produit si 'origin/main' n'existe pas encore (premier push). Utilise HEAD^ à la place.
        try:
            command = ["git", "diff", "--name-only", "HEAD^", "HEAD"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            files = result.stdout.strip().split('\n')
            
            files_to_check = [
                f for f in files 
                if f and not f.endswith(('.png', '.jpg', '.lock', '.min.js', '.map', '.log', '.md', '.env', '.gitignore', '.csv', '.json'))
            ]
            print(f"DEBUG: Fichiers détectés par HEAD^: {files_to_check}", file=sys.stderr)
            return files_to_check
        except Exception:
             # Si même HEAD^ ne fonctionne pas (ex: premier commit), on sort
            print("Avertissement: Impossible de déterminer les fichiers modifiés. Poursuite sans analyse.", file=sys.stderr)
            return []
    except Exception as e:
        print(f"Avertissement (Detection Error): {e}", file=sys.stderr)
        return []

def analyze_code_with_gemini(file_path):
    """Envoie le contenu du fichier à Gemini pour analyse et reçoit la correction."""
    
    # 1. Lire le contenu du fichier
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except FileNotFoundError:
        return f"Erreur de lecture : Le fichier {file_path} est introuvable."
    
    if not code_content.strip():
        return None # Fichier vide

    # 2. Le Prompt Clé MODIFIÉ (Plus Strict) pour Gemini
    prompt = (
        "En tant qu'expert en revue de code strict (HTML/CSS/JS/Python), analyse le fichier '" + file_path + "'. "
        "Recherche OBLIGATOIREMENT: 1) Toute **erreur de syntaxe** (balise mal orthographiée, variable non définie, etc.). 2) Toute **injection de code** d'un autre langage (ex: 'printf', PHP) dans le fichier. 3) Les failles de sécurité et les mauvaises pratiques. "
        "Si le code est absolument parfait et ne contient **aucune erreur de syntaxe ou de bonnes pratiques**, réponds UNIQUEMENT par la chaîne 'CODE_VALIDÉ'."
        "Sinon, liste CLAIREMENT TOUS les problèmes trouvés (avec le numéro de ligne si possible) et propose une **correction de code complète** pour chaque problème. "
        f"Voici le code:\n\n"
        f"```\n{code_content}\n```"
    )
    
    # 3. Appel à l'API
    try:
        client = genai.Client()
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
        
    except APIError as e:
        return f"Erreur API Gemini : {e}. Vérifiez votre clé API ou votre quota."
    except Exception as e:
        return f"Erreur inattendue : {e}"

def main():
    
    # 1. Chargement de la clé API à partir de .env
    load_dotenv()
    
    # 2. Vérification de la clé API
    if not os.getenv("GEMINI_API_KEY"):
        print("\n🛑 ERREUR CRITIQUE: La variable d'environnement GEMINI_API_KEY n'est pas définie.", file=sys.stderr)
        print("Veuillez créer un fichier .env à la racine du projet avec GEMINI_API_KEY='VOTRE_CLÉ' et vous assurer qu'elle est correcte.", file=sys.stderr)
        sys.exit(1)

    print("--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---")
    
    files_to_check = get_staged_files()
    
    # Sortie explicite si rien à analyser
    if not files_to_check:
        print("\n--- INFO HOOK : Aucun fichier de code pertinent trouvé pour l'analyse Gemini. Poursuite du push. ---")
        sys.exit(0)
    
    problem_found = False
    
    print(f"Fichiers à analyser : {', '.join(files_to_check)}")

    for file_path in files_to_check:
        print(f"\n[🔬] Analyse de {file_path}...")
        result = analyze_code_with_gemini(file_path)
        
        if result is None:
             print(f"Skippé: {file_path} (fichier vide).")
             continue
        
        # 3. Évaluation du Résultat
        if "CODE_VALIDÉ" in result:
            print(f"[✅] {file_path} : Code validé par Gemini.")
        else:
            print(f"[❌] PROBLÈME DÉTECTÉ dans {file_path} :")
            print("--------------------------------------------------")
            print(result)
            print("--------------------------------------------------")
            problem_found = True

    # 4. Décision finale du push
    if problem_found:
        print("\n!!! 🛑 PUSH ANNULÉ : Des problèmes de code critiques ont été détectés. Veuillez corriger avant de repousser. !!!")
        sys.exit(1) # Renvoyer un code d'erreur annule le push
    else:
        print("\n--- ✅ Analyse terminée. Code propre. Poursuite du push. ---")
        sys.exit(0) # Renvoyer 0 permet le push

if __name__ == "__main__":
    main()