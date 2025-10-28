# gemini_code_analyzer.py

import os
import sys
import subprocess
import json
import yaml
import copy
import hashlib
from dotenv import load_dotenv
from tqdm import tqdm
import google.generativeai as genai  # ← SDK officiel

print("DEBUT DU SCRIPT GEMINI")  # DEBUG

# --- CODES COULEUR ANSI ---
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_END = '\033[0m'

# --- FICHIERS ---
CONFIG_FILE = '.geminianalyzer.yml'
CACHE_FILE = '.gemini_cache.json'

# --- UTILITAIRES ---
def deep_merge_dicts(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge_dicts(base[key], value)
        else:
            base[key] = value
    return base

def load_config():
    default_config = {
        'analyzer': {
            'model_name': 'gemini-1.5-flash',  # ← Modèle rapide & fiable
            'max_file_size_kb': 500,
            'strict_untagged_output': False,
            'analyzable_extensions': ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.java', '.c', '.cpp', '.php', '.go', '.rb', '.sh', '.json', '.yml', '.yaml'],
        },
        'rules_override': "Aucune règle spécifique n'a été fournie."
    }
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
        merged = copy.deepcopy(default_config)
        return deep_merge_dicts(merged, user_config)
    except FileNotFoundError:
        print(f"{COLOR_YELLOW}WARN:{COLOR_END} Fichier '{CONFIG_FILE}' non trouvé → config par défaut.", file=sys.stderr)
        return default_config
    except yaml.YAMLError as e:
        print(f"{COLOR_RED}ERREUR YAML:{COLOR_END} {e} → config par défaut.", file=sys.stderr)
        return default_config

def get_project_context():
    context = ""
    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            deps = list(data.get('dependencies', {}).keys())
            if 'react' in deps or 'next' in deps:
                context += "Projet React/Next.js → respect des hooks et composants."
            elif 'express' in deps:
                context += "Projet Node.js/Express → sécurité des routes."
            else:
                context += f"Node.js avec: {', '.join(deps[:5])}."
        except:
            pass
    if os.path.exists('requirements.txt'):
        context += " Python → PEP 8 et performance."
    return context or "Aucun framework détecté → analyse générique."

# --- CACHE ---
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        print(f"{COLOR_RED}ERREUR CACHE:{COLOR_END} {e}", file=sys.stderr)

def get_file_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

# --- FICHIERS À ANALYSER ---
def get_files_and_patches(config):
    files = []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD^", "HEAD"],
            capture_output=True, text=True, check=True
        )
        for path in result.stdout.strip().split('\n'):
            if not path: continue
            if not any(path.lower().endswith(ext) for ext in config['analyzer']['analyzable_extensions']):
                continue
            if os.path.getsize(path) / 1024 > config['analyzer']['max_file_size_kb']:
                print(f"{COLOR_BLUE}IGNORÉ (taille):{COLOR_END} {path}", file=sys.stderr)
                continue

            # Patch
            patch = subprocess.run(
                ["git", "diff", "--unified=0", "HEAD^", "--", path],
                capture_output=True, text=True
            ).stdout.strip()

            if patch:
                files.append({'path': path, 'patch': patch})
            else:
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()
                    if content:
                        files.append({'path': path, 'patch': content})
                        print(f"{COLOR_YELLOW}WARN:{COLOR_END} Pas de patch → analyse complète: {path}", file=sys.stderr)
                except:
                    continue
    except:
        pass
    return files

# --- ANALYSE GEMINI ---
def analyze_code_with_gemini(file_info, config, context, cache):
    path = file_info['path']
    patch = file_info['patch']
    current_hash = get_file_hash(path)

    # CACHE
    if current_hash and path in cache and cache[path].get('sha256') == current_hash and cache[path].get('status') == 'CODE_VALIDÉ':
        return "CODE_VALIDÉ", True

    # PROMPT
    rules = config.get('rules_override', "Aucune règle spécifique.")
    prompt = (
        f"Contexte projet : {context}\n"
        f"Règles : {rules}\n\n"
        f"Analyse ce patch pour '{path}' :\n"
        "Tagge chaque problème avec [CRITICAL_ERROR] ou [WARNING].\n"
        "Si tout est bon → réponds UNIQUEMENT 'CODE_VALIDÉ'.\n\n"
        f"```diff\n{patch}\n```"
    )

    try:
        # ← CORRECTION : Utilisation directe du modèle
        model = genai.GenerativeModel(config['analyzer']['model_name'])
        response = model.generate_content(prompt)
        result = response.text.strip()

        # MISE À JOUR CACHE
        if "CODE_VALIDÉ" in result:
            cache[path] = {'sha256': current_hash, 'status': 'CODE_VALIDÉ'}
        elif path in cache:
            del cache[path]

        return result, False

    except Exception as e:
        return f"{COLOR_RED}ERREUR API:{COLOR_END} {e}", False

# --- MAIN ---
def main():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print(f"{COLOR_RED}ERREUR : GEMINI_API_KEY manquante dans .env{COLOR_END}", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    context = get_project_context()
    cache = load_cache()

    print(f"{COLOR_BLUE}--- Démarrage Gemini pre-push ---{COLOR_END}")
    print(f"{COLOR_BLUE}Contexte:{COLOR_END} {context}")

    files = get_files_and_patches(config)
    if not files:
        print(f"{COLOR_YELLOW}Aucun fichier à analyser → push autorisé.{COLOR_END}")
        sys.exit(0)

    print(f"{COLOR_BLUE}Fichiers ({len(files)}):{COLOR_END} {', '.join(f['path'] for f in files)}")

    has_critical = False
    pbar = tqdm(files, desc="Analyse", unit="fichier", ncols=100)

    for file_info in pbar:
        path = file_info['path']
        pbar.set_description(f"Analyse {os.path.basename(path)}")
        result, cached = analyze_code_with_gemini(file_info, config, context, cache)

        if cached:
            print(f"[{COLOR_BLUE}CACHE{COLOR_END}] {path} : validé")
        elif "CODE_VALIDÉ" in result:
            print(f"[{COLOR_GREEN}OK{COLOR_END}] {path}")
        else:
            critical = "[CRITICAL_ERROR]" in result
            if critical or (config['analyzer'].get('strict_untagged_output') and not any(tag in result for tag in ["[CRITICAL_ERROR]", "[WARNING]"])):
                print(f"[{COLOR_RED}BLOQUÉ{COLOR_END}] {path}")
                has_critical = True
            else:
                print(f"[{COLOR_YELLOW}AVERTISSEMENT{COLOR_END}] {path}")
            print("-" * 50 + f"\n{result}\n" + "-" * 50)

    save_cache(cache)
    pbar.close()

    if has_critical:
        print(f"\n{COLOR_RED}PUSH BLOQUÉ : Erreurs critiques détectées.{COLOR_END}")
        sys.exit(1)
    else:
        print(f"\n{COLOR_GREEN}PUSH AUTORISÉ : Code propre.{COLOR_END}")
        sys.exit(0)

if __name__ == "__main__":
    main()

print("FIN DU SCRIPT")  # DEBUG