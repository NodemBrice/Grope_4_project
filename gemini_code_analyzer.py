# gemini_code_analyzer.py

import os
import sys
import subprocess
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from tqdm import tqdm # Importation pour la barre de progression

# --- CODES COULEUR ANSI (Amélioration de l'Affichage) ---
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_END = '\033[0m'

# --- Configuration ---
MODEL_NAME = 'gemini-2.5-flash' 
MAX_FILE_SIZE_KB = 500  # Taille maximale du fichier à analyser (500 Ko)
# Extensions à analyser (autres seront ignorées)
ANALYZABLE_EXTENSIONS = ('.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.java', '.c', '.cpp', '.php', '.go', '.rb', '.sh')

# --------------------------------------------------------------------------------
# A. FILTRAGE AVANCÉ ET B. ANALYSE DIFFÉRENTIELLE
# --------------------------------------------------------------------------------

def get_files_and_patches():
    """
    Récupère la liste de tous les fichiers modifiés et génère un patch
    contenant uniquement les lignes ajoutées/modifiées (Analyse Différentielle).
    """
    files_to_process = []
    
    try:
        # Compare la HEAD locale avec l'état distant connu (commits à pousser)
        command = ["git", "diff", "--name-only", "origin/main...HEAD"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
        
    except subprocess.CalledProcessError:
        # Fallback pour le premier push (pas d'origin/main encore)
        try:
            command = ["git", "diff", "--name-only", "HEAD^", "HEAD"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            files = result.stdout.strip().split('\n')
        except Exception:
            return []

    for file_path in files:
        if not file_path:
            continue
            
        # 1. Filtrage Avancé : Taille et Extension
        
        # Vérification par extension
        if not any(file_path.lower().endswith(ext) for ext in ANALYZABLE_EXTENSIONS):
            # print(f"{COLOR_BLUE}INFO:{COLOR_END} Fichier ignoré (extension non pertinente): {file_path}", file=sys.stderr)
            continue
            
        # Vérification par taille (pour ignorer les gros binaires/dépendances)
        try:
            file_size_kb = os.path.getsize(file_path) / 1024
            if file_size_kb > MAX_FILE_SIZE_KB:
                print(f"{COLOR_BLUE}INFO:{COLOR_END} Fichier ignoré (taille > {MAX_FILE_SIZE_KB}KB): {file_path}", file=sys.stderr)
                continue
        except FileNotFoundError:
            continue

        # 2. Analyse Différentielle : Génération du patch
        try:
            # Récupère uniquement les lignes modifiées/ajoutées (le "patch")
            patch_command = ["git", "diff", "--unified=0", "origin/main...HEAD", file_path]
            patch_result = subprocess.run(patch_command, capture_output=True, text=True, check=True)
            
            patch_content = patch_result.stdout.strip()

            if not patch_content:
                # Si le fichier est listé mais que le patch est vide, c'est probablement un fichier
                # que Git ne suit plus ou qui n'a pas été modifié de manière significative.
                continue

            files_to_process.append({
                'path': file_path,
                'patch': patch_content
            })

        except subprocess.CalledProcessError as e:
            # Fallback en cas d'erreur de diff (comme pour un fichier nouvellement créé sans base)
            print(f"{COLOR_YELLOW}WARN:{COLOR_END} Impossible de générer le patch pour {file_path}. Analyse du fichier entier.", file=sys.stderr)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    full_content = f.read()
                files_to_process.append({
                    'path': file_path,
                    'patch': f"--- {file_path} ---\nContenu complet pour analyse:\n{full_content}"
                })
            except Exception:
                continue

    return files_to_process

def analyze_code_with_gemini(file_info):
    """Envoie le patch (ou le contenu) à Gemini pour analyse."""
    file_path = file_info['path']
    patch_content = file_info['patch']

    # Le prompt est maintenant basé sur le patch, pas le fichier complet
    prompt = (
        "En tant qu'expert polyvalent en développement informatique et web (HTML, CSS, JavaScript, Python, etc.), "
        "analyse les MODIFICATIONS (patch) fournies ci-dessous pour le fichier '" + file_path + "'. "
        
        "**Ta mission est de te concentrer UNIQUEMENT sur les aspects techniques du codage introduits par ces changements :** "
        "1. **Erreurs de Fonctionnalité/Syntaxe :** Bugs, variables non définies, erreurs de syntaxe spécifiques au langage. "
        "2. **Sécurité :** Failles potentielles ou injections. "
        "3. **Bonnes Pratiques/Maintenabilité :** Non-conformité aux standards du langage. "
        
        "**IGNORE TOUT LE CONTENU TEXTUEL et les erreurs de langue naturelle (fautes d'orthographe, grammaire) dans les commentaires ou le contenu HTML.** "
        
        "Si les changements sont techniquement sains et n'introduisent AUCUN problème, réponds UNIQUEMENT par la chaîne 'CODE_VALIDÉ'."
        "Sinon, liste CLAIREMENT TOUS les problèmes techniques trouvés (avec le numéro de ligne si possible) et propose une **correction de code complète** pour le fichier entier ou des suggestions claires pour chaque problème. "
        f"Voici les modifications (patch):\n\n"
        f"```diff\n{patch_content}\n```"
    )
    
    # Appel à l'API
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
        
    except APIError as e:
        return f"{COLOR_RED}Erreur API Gemini:{COLOR_END} {e}. Vérifiez votre clé API ou votre quota."
    except Exception as e:
        return f"{COLOR_RED}Erreur inattendue:{COLOR_END} {e}"

# --------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------

def main():
    
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"):
        print(f"\n{COLOR_RED}🛑 ERREUR CRITIQUE:{COLOR_END} La variable d'environnement GEMINI_API_KEY n'est pas définie.", file=sys.stderr)
        print("Veuillez créer un fichier .env à la racine du projet.", file=sys.stderr)
        sys.exit(1)

    print(f"{COLOR_BLUE}--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---{COLOR_END}")
    
    files_to_analyze = get_files_and_patches()
    
    if not files_to_analyze:
        print(f"\n{COLOR_YELLOW}--- INFO HOOK : Aucun fichier de code pertinent trouvé pour l'analyse Gemini. Poursuite du push. ---{COLOR_END}")
        sys.exit(0)
    
    problem_found = False
    
    print(f"{COLOR_BLUE}Fichiers à analyser ({len(files_to_analyze)}) : {COLOR_END}{', '.join([f['path'] for f in files_to_analyze])}")

    # Utilisation de tqdm pour la barre de progression (UX Améliorée)
    progress_bar = tqdm(files_to_analyze, desc=f"{COLOR_BLUE}Analyse en cours{COLOR_END}", unit="file", ncols=100)
    
    for file_info in progress_bar:
        file_path = file_info['path']
        
        # Mise à jour du libellé de la barre de progression
        progress_bar.set_description(f"{COLOR_BLUE}Analyse de {file_path.split('/')[-1]}{COLOR_END}")

        # L'analyse réelle et l'appel API
        result = analyze_code_with_gemini(file_info)
        
        # Efface la ligne de progression pour afficher le résultat
        progress_bar.clear()
        
        # Évaluation du Résultat
        if "CODE_VALIDÉ" in result:
            print(f"[{COLOR_GREEN}✅{COLOR_END}] {file_path} : Code validé par Gemini.")
        else:
            print(f"[{COLOR_RED}❌{COLOR_END}] {file_path} : {COLOR_RED}PROBLÈME DÉTECTÉ !{COLOR_END}")
            print("-" * 50)
            print(result)
            print("-" * 50)
            problem_found = True
        
        # Réaffiche la barre de progression après le message (sauf pour le dernier élément)
        if progress_bar.n < len(files_to_analyze):
            progress_bar.display()

    progress_bar.close()

    # Décision finale du push
    if problem_found:
        print(f"\n{COLOR_RED}!!! 🛑 PUSH ANNULÉ : Des problèmes de code critiques ont été détectés. Veuillez corriger avant de repousser. !!!{COLOR_END}")
        sys.exit(1) 
    else:
        print(f"\n{COLOR_GREEN}--- ✅ Analyse terminée. Code propre. Poursuite du push. ---{COLOR_END}")
        sys.exit(0)

if __name__ == "__main__":
    main()