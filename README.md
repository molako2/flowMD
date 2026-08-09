# flowMD

**Convertissez vos PDF en Markdown, Word et Excel — français, arabe, anglais — 100 % en local.**

flowMD est une application locale d'OCR et de conversion de documents. Elle transforme vos PDF
(y compris les documents **scannés**) en fichiers **Markdown (.md)**, **Word (.docx)** et
**Excel (.xlsx)**, avec détection de la structure du document : titres, paragraphes, **tableaux**,
images. Aucune donnée ne quitte votre machine — aucun service en ligne, aucun abonnement.

- 🇫🇷 🇲🇦 🇬🇧 OCR en **français, arabe et anglais** (moteurs interchangeables)
- 📊 Les tableaux détectés deviennent de **vrais tableaux** (onglets Excel, tableaux Word/Markdown)
- 🖥️ **Interface web en français** : glisser-déposer, progression, aperçu (avec sens de lecture RTL), téléchargements
- ⌨️ **Ligne de commande** pour les conversions en série
- 🔒 **100 % local** : idéal pour les documents confidentiels (comptabilité, audit, juridique)

Le cœur de l'analyse est [Docling](https://github.com/docling-project/docling) (IBM, licence MIT),
la référence open source pour la conversion structurée de documents, associé aux moteurs OCR
[EasyOCR](https://github.com/JaidedAI/EasyOCR) (inclus) et
[Tesseract](https://github.com/tesseract-ocr/tesseract) (facultatif, recommandé pour les
documents mêlant arabe et français).

---

## Installation

### Option A — Windows (recommandée pour les non-développeurs)

1. Installez [Python 3.11+](https://www.python.org/downloads/) (cochez **« Add python.exe to PATH »**).
2. Téléchargez ce dépôt (Code → Download ZIP) et décompressez-le.
3. Double-cliquez sur **`start.bat`**.

Le script crée l'environnement, installe les dépendances, télécharge les modèles d'analyse
(~2 Go, **une seule fois**) puis ouvre l'interface dans votre navigateur.

> 💡 **Documents mêlant arabe et français ?** Installez aussi
> [Tesseract pour Windows](https://github.com/UB-Mannheim/tesseract/wiki) en cochant les langues
> *Arabic* et *French* lors de l'installation. flowMD le détecte automatiquement.

### Option B — Linux / macOS

```bash
git clone https://github.com/molako2/flowMD.git
cd flowMD
./start.sh
```

### Option C — Docker (tout inclus, hors ligne après construction)

```bash
docker compose up --build
```

Puis ouvrez <http://localhost:8000>. L'image contient Tesseract (ara/fra/eng) **et** les modèles
déjà téléchargés : après la construction, plus aucun accès réseau n'est nécessaire.

---

## Utilisation

### Interface web

```bash
flowmd serve --open-browser
```

1. Glissez un ou plusieurs PDF dans la zone de dépôt.
2. Choisissez les **langues** du document (français / arabe / anglais), les **formats** de sortie
   et, pour un document scanné, activez **« Forcer l'OCR »**.
3. Cliquez sur **Convertir**, suivez la progression, prévisualisez le résultat et téléchargez
   chaque format ou tout en ZIP.

### Ligne de commande

```bash
# Conversion complète (Markdown + Word + Excel)
flowmd convert facture.pdf

# Document scanné en arabe, sortie Word uniquement
flowmd convert scan.pdf --langs ar --to docx --force-ocr

# Plusieurs fichiers, moteur Tesseract explicite
flowmd convert *.pdf --langs fr,ar --engine tesseract --out ./resultats

# Diagnostic de l'installation
flowmd doctor

# Téléchargement des modèles (~2 Go, une seule fois)
flowmd setup
```

---

## Langues et moteurs OCR

| Moteur | Installation | fr | ar | en | ar + fr ensemble |
|---|---|---|---|---|---|
| **EasyOCR** (par défaut) | incluse avec flowMD | ✔ | ✔ | ✔ | ✖ (limitation d'EasyOCR) |
| **Tesseract** (recommandé pour les docs mixtes) | facultative (binaire système) | ✔ | ✔ | ✔ | ✔ |

Le moteur **auto** choisit intelligemment : Tesseract dès qu'il est disponible et que l'arabe est
demandé, EasyOCR sinon. Si vous demandez **arabe + français avec EasyOCR seul**, flowMD bascule
automatiquement sur Tesseract, ou — s'il est absent — poursuit en arabe + anglais en vous
l'indiquant clairement.

## Benchmark

Résultats sur les échantillons du dépôt (`tests/samples/`, OCR pleine page forcé) — à reproduire
chez vous avec `python scripts/benchmark_engines.py` :

_À compléter : exécutez le benchmark après `flowmd setup` et collez le tableau ici._

---

## Pour les développeurs

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                    # tests rapides (sans modèles)
pytest -m integration     # tests complets (vrais modèles, lents)

# Frontend (interface French/Vite/React) — le build est committé
cd frontend && npm install && npm run build
```

Architecture :

```
src/flowmd/
├── languages.py      # normalisation fr/ar/en + règles de compatibilité moteur
├── engines.py        # détection EasyOCR/Tesseract, options Docling
├── pipeline.py       # PDF → DoclingDocument (cache de convertisseurs)
├── exporters/        # markdown.py, docx.py (pandoc + RTL), xlsx.py (openpyxl)
├── jobs.py           # file de jobs en mémoire, worker unique
├── cli.py            # commandes convert / serve / setup / doctor
├── server/           # API FastAPI + interface web statique
└── web/static/       # build du frontend (committé)
```

## Limites connues

- **Documents scannés volumineux** : le traitement est séquentiel et s'exécute sur CPU ;
  comptez plusieurs secondes par page en OCR forcé.
- **Ordre de lecture arabe** : sur des mises en page complexes (multi-colonnes), l'ordre du texte
  peut nécessiter une relecture. L'export Word reste éditable ; l'aperçu propose un bouton RTL.
- **EasyOCR arabe + français** : combinaison impossible dans un même passage (limitation du
  moteur) — installez Tesseract pour les documents mixtes.
- La première conversion sans `flowmd setup` déclenche le téléchargement des modèles et peut
  sembler bloquée : préférez toujours `flowmd setup` (ou `start.bat`, qui s'en charge).

## Licence

MIT — voir [LICENSE](LICENSE). Docling est distribué sous licence MIT ; EasyOCR sous Apache 2.0 ;
Tesseract sous Apache 2.0 ; la police d'exemple Noto Naskh Arabic sous licence SIL OFL.
