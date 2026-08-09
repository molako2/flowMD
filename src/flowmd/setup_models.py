"""Téléchargement explicite des modèles (~2 Go) : Docling + EasyOCR.

Évite qu'une première conversion semble « bloquée » pendant un téléchargement
silencieux. Utilisé par `flowmd setup`, start.bat/start.sh et le Dockerfile.
"""

from __future__ import annotations

from .config import Settings

# Paires de langues pré-téléchargées pour EasyOCR (l'arabe ne se combine
# qu'avec l'anglais — voir languages.plan_ocr).
EASYOCR_LANG_SETS: tuple[tuple[str, ...], ...] = (("fr", "en"), ("ar", "en"))


def download_docling_models(settings: Settings, echo=print) -> None:
    from docling.utils.model_downloader import download_models

    target = settings.docling_artifacts_dir
    target.mkdir(parents=True, exist_ok=True)
    echo(f"Téléchargement des modèles Docling (mise en page, tableaux) vers {target} …")
    download_models(output_dir=target, progress=True)
    echo("Modèles Docling prêts.")


def download_easyocr_models(settings: Settings, echo=print) -> None:
    import easyocr

    target = settings.easyocr_models_dir
    target.mkdir(parents=True, exist_ok=True)
    for lang_set in EASYOCR_LANG_SETS:
        echo(f"Téléchargement des modèles EasyOCR ({'+'.join(lang_set)}) vers {target} …")
        easyocr.Reader(
            list(lang_set),
            gpu=settings.easyocr_gpu,
            model_storage_directory=str(target),
            download_enabled=True,
            verbose=False,
        )
    echo("Modèles EasyOCR prêts.")


def download_paddleocr_models(settings: Settings, echo=print) -> None:
    """Pré-télécharge les modèles PaddleOCR (PP-OCRv6/v5) si le moteur est installé."""
    from .engines import paddleocr_available

    if not paddleocr_available():
        return
    from paddleocr import PaddleOCR

    # « fr » couvre le modèle latin unifié PP-OCRv6 (français + anglais) ;
    # « ar » déclenche le modèle arabe (PP-OCRv5, repli automatique).
    for lang in ("fr", "ar", "en"):
        echo(f"Téléchargement des modèles PaddleOCR ({lang}) …")
        try:
            PaddleOCR(
                lang=lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
            )
        except Exception as exc:
            echo(f"  Avertissement : modèles PaddleOCR ({lang}) non téléchargés ({exc}).")
    echo("Modèles PaddleOCR prêts.")


# Données de langue officielles Tesseract (dépôt tessdata_fast, licence Apache 2.0)
TESSDATA_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/{code}.traineddata"


def download_tesseract_langs(settings: Settings, echo=print) -> None:
    """Complète les données de langue ara/fra/eng manquantes de Tesseract.

    Ne fait rien si Tesseract est absent. Écrit dans le dossier tessdata à côté
    du binaire (installations « portables » ou utilisateur) ; en cas de refus
    d'écriture (ex. Program Files sans droits admin), explique quoi faire.
    """
    import urllib.request
    from pathlib import Path

    from .engines import probe_tesseract
    from .languages import _TESSERACT_CODES  # noqa: PLC2701

    tess = probe_tesseract()
    if not tess.available or not tess.cmd:
        return
    missing = [code for pub, code in _TESSERACT_CODES.items() if pub not in tess.langs]
    if not missing:
        return

    tessdata = Path(tess.cmd).parent / "tessdata"
    if not tessdata.is_dir():
        echo(f"Avertissement : dossier tessdata introuvable ({tessdata}) — langues non complétées.")
        return

    for code in missing:
        url = TESSDATA_URL.format(code=code)
        echo(f"Téléchargement de la langue Tesseract « {code} » …")
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                data = response.read()
            (tessdata / f"{code}.traineddata").write_bytes(data)
        except PermissionError:
            echo(
                f"Avertissement : impossible d'écrire dans {tessdata} (droits insuffisants). "
                "Relancez l'installateur Tesseract et cochez Arabic/French, ou copiez "
                f"manuellement {code}.traineddata dans ce dossier."
            )
            return
        except Exception as exc:
            echo(f"Avertissement : langue « {code} » non téléchargée ({exc}).")
    echo("Langues Tesseract complétées.")


def setup_all(settings: Settings, echo=print) -> None:
    settings.ensure_dirs()
    download_docling_models(settings, echo=echo)
    download_easyocr_models(settings, echo=echo)
    download_paddleocr_models(settings, echo=echo)
    download_tesseract_langs(settings, echo=echo)
    echo("Installation des modèles terminée : flowMD peut fonctionner hors ligne.")
