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


def setup_all(settings: Settings, echo=print) -> None:
    settings.ensure_dirs()
    download_docling_models(settings, echo=echo)
    download_easyocr_models(settings, echo=echo)
    echo("Installation des modèles terminée : flowMD peut fonctionner hors ligne.")
