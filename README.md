🤖 Analyse de Code Pré-Push avec Gemini
Ce projet utilise un hook Git pre-push pour analyser automatiquement le code de vos commits via l'API Google Gemini avant qu'ils n'atteignent le dépôt distant. Si Gemini détecte des erreurs de syntaxe, des failles de sécurité, ou des mauvaises pratiques, le push est bloqué.

🚀 Installation et Configuration
Suivez ces étapes pour mettre en place l'environnement et activer le hook.

1. Prérequis
Vous devez avoir installé :

Git (version 2.x ou supérieure)

Python (version 3.8 ou supérieure)

Une Clé API Gemini que vous pouvez obtenir via Google AI Studio.

2. Configuration de l'Environnement Python
Il est fortement recommandé d'utiliser un environnement virtuel (venv) pour isoler les dépendances du projet.

Créez et activez l'environnement virtuel :

Bash

python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# ou
.\venv\Scripts\activate    # Windows
Installez les dépendances nécessaires (SDK Google GenAI et python-dotenv) :

Bash

pip install google-genai python-dotenv
3. Gestion de la Clé API (Sécurité) 🔑
Votre clé API est un secret et ne doit jamais être committée dans votre dépôt Git.

Créez un fichier .env à la racine de votre projet.

Ajoutez votre clé API à ce fichier :

Extrait de code

# .env
GEMINI_API_KEY="VOTRE_CLÉ_SECRÈTE_ICI"
Vérifiez que le fichier .gitignore contient la ligne .env pour éviter toute fuite.

⚙️ Activation du Hook Git
Le hook est le script Shell qui lance le processus d'analyse.

Copiez les fichiers suivants à la racine de votre projet :

gemini_code_analyzer.py (votre script Python)

Créez le fichier de hook dans le répertoire .git/hooks/ :

Le fichier doit être nommé pre-push (sans extension).

Collez le contenu suivant dans .git/hooks/pre-push (assurez-vous d'être sur des chemins relatifs à la racine du projet) :

Bash

#!/bin/bash

# Le hook s'exécute depuis la racine du dépôt.

PYTHON_SCRIPT_PATH="gemini_code_analyzer.py"
VENV_PYTHON="venv/bin/python" 

# Tente d'utiliser l'interpréteur Python de l'environnement virtuel
if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$PYTHON_SCRIPT_PATH"
else
    echo "Avertissement: Environnement virtuel ('$VENV_PYTHON') non trouvé ou non exécutable. Utilisation de python3 global."
    python3 "$PYTHON_SCRIPT_PATH"
fi

# Récupère le code de sortie du script Python
RESULTAT=$?

if [ $RESULTAT -ne 0 ]; then
    echo ""
    echo "### 🛑 PUSH BLOQUÉ : Veuillez corriger les problèmes de code. ###"
    exit 1 # Annule le push
fi

exit 0 # Autorise le push
Rendez le hook exécutable (obligatoire !) :

Bash

chmod +x .git/hooks/pre-push
🧪 Utilisation et Tests
Le hook est désormais actif. Il se déclenchera automatiquement à chaque fois que vous exécutez git push.

Cas 1 : Code Propre (Push Réussi)
Si votre code est valide ou si vous n'avez modifié aucun fichier de code :

Bash

git push origin main
Résultat :

--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---
...
--- ✅ Analyse terminée. Code propre. Poursuite du push. ---
... (Messages de Git et push réussi) ...
Cas 2 : Code Contenant des Erreurs (Push Bloqué)
Pour tester l'échec, introduisez volontairement une erreur de syntaxe (<af hrekf...>, print('test) ou une ligne dangereuse.

Commitez l'erreur : git commit -am "Code avec erreur de test"

Tentez de pousser : git push origin main

Résultat : Le push sera bloqué par le hook.

--- 🚀 Démarrage de l'analyse de code par Gemini (pre-push) ---
...
[❌] PROBLÈME DÉTECTÉ dans international.html :
--------------------------------------------------
Problème 1: Balise a mal orthographiée...
... (Explications de Gemini) ...
--------------------------------------------------
!!! 🛑 PUSH ANNULÉ : Des problèmes de code critiques ont été détectés... !!!
### 🛑 PUSH BLOQUÉ : Veuillez corriger les problèmes de code. ###
error: failed to push some refs to '...'
Vous serez forcé de corriger le code et de committer à nouveau avant de pouvoir pousser.
