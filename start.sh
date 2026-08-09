#!/usr/bin/env bash
# ============================================================
#  flowMD - Démarrage sous Linux / macOS
#  Crée l'environnement, installe les dépendances, télécharge
#  les modèles au premier lancement, puis ouvre l'interface.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERREUR] python3 est introuvable. Installez Python 3.11 ou plus récent." >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Création de l'environnement Python…"
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import flowmd" >/dev/null 2>&1; then
    echo "Installation de flowMD et de ses dépendances (quelques minutes)…"
    python -m pip install --quiet --upgrade pip
    pip install -e .
fi

if [ ! -d data/models/docling ]; then
    echo
    echo "Premier lancement : téléchargement des modèles d'analyse (~2 Go)."
    echo "Cette étape n'a lieu qu'une seule fois."
    echo
    flowmd setup
fi

echo
echo "Démarrage de flowMD sur http://127.0.0.1:8000 …"
exec flowmd serve --open-browser
