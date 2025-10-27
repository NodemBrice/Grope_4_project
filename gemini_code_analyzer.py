# gemini_code_analyzer.py

import os
import sys
import subprocess
import json
import yaml # Nécessite 'pip install pyyaml'
import copy # Nécessite l'importation pour deepcopy
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from tqdm import tqdm # Nécessite 'pip install tqdm'

# --- CODES COULEUR ANSI ---
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_END = '\033[0m'

# --- Configuration par défaut et globale ---
CONFIG_FILE = '.geminianalyzer.yml'

# Nouvelle fonction utilitaire pour la fusion profonde
def deep_merge_dicts(base, override):
    """
    Fusionne récursivement le dictionnaire 'override' dans le dictionnaire 'base'.
    Les valeurs de 'override' prévalent en cas de conflit.
    """
    for key, value in override.items():
        # Si la valeur est un dictionnaire et existe aussi dans la base comme dictionnaire, on merge
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge_dicts(base[key], value)
        # Sinon, on remplace ou ajoute la clé/valeur
        else:
            base[key] = value
    return base

def load_config():
    """Charge la configuration depuis .geminianalyzer.yml ou utilise les valeurs par défaut."""
    default_config = {
        'analyzer': {
            'model_name': 'gemini-2.5-flash',
            'max_file_size_kb': 500,
            # Correction WARNING: Rétablissement d'une liste d'extensions par défaut complète
            'analyzable_extensions': ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.java', '.c', '.cpp', '.php', '.go', '.rb', '.sh', '.json', '.yml', '.yaml'],
        },
        'rules_override': "Aucune règle spécifique n'a été fournie."
    }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            user_config = yaml.safe_load(f)
        
        # Correction CRITICAL_ERROR: Utilisation de la copie profonde pour fusionner la config
        merged_config = copy.deepcopy(default_config)
        
        if user_config and isinstance(user_config, dict):
            return deep_merge_dicts(merged_config, user_config)
        
        return default_config
    except FileNotFoundError:
        print(f"{COLOR_YELLOW}WARN:{COLOR_END} Fichier de configuration '{CONFIG_FILE}' non trouvé. Utilisation des paramètres par défaut.", file=sys.stderr)
        return default_config
    except yaml.YAMLError as e: # Capture spécifique des erreurs de parsing
        print(f"{COLOR_RED}ERREUR CONFIG:{COLOR_END} Erreur de lecture YAML: {e}. Utilisation des paramètres par défaut.", file=sys.stderr)
        return default_config
    except Exception as e:
        print(f"{COLOR_RED}ERREUR CONFIG:{COLOR_END} Erreur inattendue lors du chargement de la configuration: {e}. Utilisation des paramètres par défaut.", file=sys.stderr)
        return default_config

def get_project_context():
    """Détecte les frameworks principaux pour fournir du contexte à Gemini."""
    context = ""
    
    # 1. Contexte Node/Web (package.json)
    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r') as f:
                data = json.load(f)
            
            dependencies = list(data.get('dependencies', {}).keys())
            
            if 'react' in dependencies or 'next' in dependencies:
                context += "Le projet est un projet web front-end, probablement React/Next.js. Les fichiers JavaScript doivent respecter les règles des hooks et des composants fonctionnels."
            elif 'express' in dependencies:
                context += "Le projet est un projet Node.js/Express. Les bonnes pratiques du serveur (gestion des routes, sécurité) sont prioritaires."
            else:
                context += f"Le projet utilise Node.js avec les dépendances principales: {', '.join(dependencies[:5])}."

        except (json.JSONDecodeError, IOError): # Correction WARNING: Gestion spécifique des exceptions
            pass 

    # 2. Contexte Python (requirements.txt) - peut être étendu
    if os.path.exists('requirements.txt'):
        context += " Le projet utilise Python. Les règles de la PEP 8 et l'efficacité du code sont importantes."
        
    if not context:
        context = "Aucun framework détecté. Analyse selon les standards généraux du langage."
        
    return context

def get_files_and_patches(config):
    """
    Récupère la liste de tous les fichiers modifiés, filtre selon la config, 
    et génère le patch (avec fallback vers l'analyse complète).
    """
    files_to_process = []
    
    # 1. Détermine les fichiers modifiés (utilisation de 'origin/main...HEAD' ou 'HEAD^')
    try:
        command = ["git", "diff", "--name-only", "origin/main...HEAD"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        try:
            command = ["git", "diff", "--name-only", "HEAD^", "HEAD"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            files = result.stdout.strip().split('\n')
        except Exception:
            return []

    for file_path in files:
        if not file_path: continue
            
        # 2. Filtrage Avancé : Taille et Extension
        analyzable_exts = config['analyzer']['analyzable_extensions']
        max_size_kb = config['analyzer']['max_file_size_kb']

        if not any(file_path.lower().endswith(ext) for ext in analyzable_exts): continue
            
        try:
            file_size_kb = os.path.getsize(file_path) / 1024
            if file_size_kb > max_size_kb:
                print(f"{COLOR_BLUE}INFO:{COLOR_END} Fichier ignoré (taille > {max_size_kb}KB): {file_path}", file=sys.stderr)
                continue
        except FileNotFoundError: continue

        # 3. Analyse Différentielle : Tentative de patch puis Fallback (Correction CRITICAL_ERROR)
        try:
            # Tente de récupérer uniquement les lignes modifiées/ajoutées (le "patch")
            # Utiliser la comparaison 'HEAD^' si le référentiel est très jeune
            patch_command = ["git", "diff", "--unified=0", "HEAD^", "--", file_path]
            patch_result = subprocess.run(patch_command, capture_output=True, text=True, check=True, errors='ignore')
            patch_content = patch_result.stdout.strip()
            
            if patch_content:
                files_to_process.append({ 'path': file_path, 'patch': patch_content })
            else:
                # Si le patch est vide, c'est peut-être un nouveau fichier. Tente d'analyser le contenu complet.
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    full_content = f.read()
                
                if full_content.strip(): # S'assure que le fichier n'est pas vide
                    files_to_process.append({ 
                        'path': file_path, 
                        'patch': full_content 
                    })
                    print(f"{COLOR_YELLOW}WARN:{COLOR_END} Pas de patch détecté pour {file_path}. Analyse complète du fichier.", file=sys.stderr)


        except subprocess.CalledProcessError:
             # Si git diff échoue complètement (référentiel très jeune ou autre problème), on analyse le fichier entier
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    full_content = f.read()
                
                if full_content.strip():
                    files_to_process.append({
                        'path': file_path,
                        'patch': full_content 
                    })
                    print(f"{COLOR_YELLOW}WARN:{COLOR_END} Impossible de générer le patch pour {file_path}. Analyse du fichier entier.", file=sys.stderr)
            except Exception:
                continue # Ignore le fichier s'il ne peut être lu

    return files_to_process

def analyze_code_with_gemini(file_info, config, context):
    """Envoie le patch à Gemini en utilisant la configuration et le contexte du projet."""
    file_path = file_info['path']
    patch_content = file_info['patch']
    
    rules_override = config.get('rules_override', "Aucune règle spécifique n'a été fournie.")

    # 1. Le Prompt Clé (avec Classification ERREUR/WARNING)
    prompt = (
        "En tant qu'expert en revue de code pour le projet ayant le contexte suivant: (" + context + "). "
        "Analyse les MODIFICATIONS (patch) fournies pour le fichier '" + file_path + "'. "
        
        "**Règles du Projet :** " + rules_override + " "
        
        "**Ton analyse doit obligatoirement classer chaque problème en deux niveaux :** "
        "1. **[CRITICAL_ERROR]** : Erreur de syntaxe, faille de sécurité, bug fonctionnel évident, ou non-conformité à une règle critique. (DOIT bloquer le push) "
        "2. **[WARNING]** : Problème de style, d'optimisation mineure ou non-conformité à une bonne pratique non critique. (PEUT être ignoré, mais doit être signalé) "
        
        "Si les changements sont techniquement sains, réponds UNIQUEMENT par la chaîne 'CODE_VALIDÉ'."
        "Sinon, liste CLAIREMENT TOUS les problèmes trouvés en commençant chaque entrée par son tag ([CRITICAL_ERROR] ou [WARNING]). "
        "Propose ensuite une correction de code complète ou des suggestions claires pour chaque problème. "
        f"Voici les modifications (patch):\n\n"
        f"```diff\n{patch_content}\n```"
    )
    
    # Appel à l'API
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=config['analyzer']['model_name'],
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
    config = load_config()
    context = get_project_context()
    
    # Correction WARNING: Rétablissement d'une instruction claire pour la clé API
    # Note: La variable d'environnement doit être GEMINI_API_KEY et non GOOGLE_API_KEY
    if not os.getenv("GEMINI_API_KEY"):
        print(f"\n{COLOR_RED}🛑 ERREUR CRITIQUE:{COLOR_END} La variable d'environnement GEMINI_API_KEY n'est pas définie.", file=sys.stderr)
        print(f"Veuillez la définir (par exemple, dans un fichier .env à la racine du projet).", file=sys.stderr)
        sys.exit(1)

    print(f"{COLOR_BLUE}--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---{COLOR_END}")
    print(f"{COLOR_BLUE}Contexte du Projet: {COLOR_END}{context}")
    
    files_to_analyze = get_files_and_patches(config)
    
    if not files_to_analyze:
        print(f"\n{COLOR_YELLOW}--- INFO HOOK : Aucun fichier pertinent trouvé. Poursuite du push. ---{COLOR_END}")
        sys.exit(0)
    
    has_critical_error = False
    
    print(f"{COLOR_BLUE}Fichiers à analyser ({len(files_to_analyze)}) : {COLOR_END}{', '.join([f['path'] for f in files_to_analyze])}")

    # Utilisation de tqdm pour la barre de progression (UX Améliorée)
    progress_bar = tqdm(
        files_to_analyze, 
        desc=f"{COLOR_BLUE}Analyse en cours{COLOR_END}", 
        unit="file", 
        ncols=100,
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
    )
    
    for file_info in progress_bar:
        file_path = file_info['path']
        
        progress_bar.set_description(f"Analyse de {file_path.split('/')[-1]}")
        result = analyze_code_with_gemini(file_info, config, context)
        
        progress_bar.clear()
        
        # --- LOGIQUE DE CLASSIFICATION (WARNINGS vs ERRORS) ---
        if "CODE_VALIDÉ" in result:
            print(f"[{COLOR_GREEN}✅{COLOR_END}] {file_path} : Code validé par Gemini.")
        else:
            # Recherche des erreurs critiques
            if "[CRITICAL_ERROR]" in result:
                print(f"[{COLOR_RED}🛑{COLOR_END}] {file_path} : {COLOR_RED}ERREURS CRITIQUES DÉTECTÉES !{COLOR_END}")
                has_critical_error = True
            elif "[WARNING]" in result:
                print(f"[{COLOR_YELLOW}⚠️{COLOR_END}] {file_path} : {COLOR_YELLOW}Avertissements de style/optimisation !{COLOR_END}")
            else:
                 # Si l'IA n'a pas utilisé les tags, on considère ça comme un warning (moins bloquant que l'erreur critique)
                print(f"[{COLOR_YELLOW}⚠️{COLOR_END}] {file_path} : {COLOR_YELLOW}Avertissements (non classifiés) !{COLOR_END}")

            print("-" * 50)
            print(result)
            print("-" * 50)
        
        progress_bar.display()

    progress_bar.close()

    # Décision finale du push : Bloque uniquement si CRITICAL_ERROR est trouvé
    if has_critical_error:
        print(f"\n{COLOR_RED}!!! 🛑 PUSH ANNULÉ : Des ERREURS CRITIQUES ont été détectées. !!!{COLOR_END}")
        sys.exit(1) 
    else:
        print(f"\n{COLOR_GREEN}--- ✅ Analyse terminée. Code propre (ou seulement des avertissements). Poursuite du push. ---{COLOR_END}")
        sys.exit(0)

if __name__ == "__main__":
    main()