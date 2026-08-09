"""Détection des moteurs OCR disponibles et fabrique des options Docling."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from dataclasses import dataclass, field

from .config import Settings
from .languages import _TESSERACT_CODES, OcrPlan  # noqa: PLC2701

_TESS_PUBLIC_BY_CODE = {v: k for k, v in _TESSERACT_CODES.items()}


@dataclass
class TesseractInfo:
    available: bool
    cmd: str | None = None
    version: str | None = None
    langs: set[str] = field(default_factory=set)  # codes publics fr/ar/en


def probe_tesseract() -> TesseractInfo:
    """Cherche le binaire tesseract et les données de langue ara/fra/eng."""
    cmd = shutil.which("tesseract")
    if not cmd:
        return TesseractInfo(available=False)
    try:
        version_out = subprocess.run(
            [cmd, "--version"], capture_output=True, text=True, timeout=10
        )
        version = version_out.stdout.splitlines()[0].strip() if version_out.stdout else None
        langs_out = subprocess.run(
            [cmd, "--list-langs"], capture_output=True, text=True, timeout=10
        )
        installed = {
            line.strip()
            for line in langs_out.stdout.splitlines()
            if line.strip() and not line.lower().startswith("list of")
        }
        public = {_TESS_PUBLIC_BY_CODE[code] for code in installed if code in _TESS_PUBLIC_BY_CODE}
        return TesseractInfo(available=True, cmd=cmd, version=version, langs=public)
    except (OSError, subprocess.SubprocessError):
        return TesseractInfo(available=False)


def easyocr_available() -> bool:
    return importlib.util.find_spec("easyocr") is not None


def docling_available() -> bool:
    return importlib.util.find_spec("docling") is not None


def models_ready(settings: Settings) -> bool:
    """Heuristique : les modèles Docling ont-ils déjà été téléchargés ?"""
    docling_dir = settings.docling_artifacts_dir
    return docling_dir.is_dir() and any(docling_dir.iterdir())


def build_ocr_options(plan: OcrPlan, settings: Settings, force_ocr: bool = False):
    """Construit les options OCR Docling correspondant au plan (import paresseux)."""
    if plan.engine == "tesseract":
        from docling.datamodel.pipeline_options import TesseractCliOcrOptions

        return TesseractCliOcrOptions(
            lang=plan.engine_lang_codes,
            force_full_page_ocr=force_ocr,
        )

    from docling.datamodel.pipeline_options import EasyOcrOptions

    settings.easyocr_models_dir.mkdir(parents=True, exist_ok=True)
    return EasyOcrOptions(
        lang=plan.engine_lang_codes,
        force_full_page_ocr=force_ocr,
        use_gpu=settings.easyocr_gpu,
        model_storage_directory=str(settings.easyocr_models_dir),
        download_enabled=True,
    )


def engines_status(settings: Settings) -> dict:
    """État des moteurs pour l'API /api/engines et `flowmd doctor`."""
    tess = probe_tesseract()
    easy = easyocr_available()
    return {
        "engines": [
            {
                "id": "auto",
                "label": "Automatique (recommandé)",
                "available": easy or tess.available,
                "detail": "Choisit le meilleur moteur selon les langues demandées.",
            },
            {
                "id": "easyocr",
                "label": "EasyOCR",
                "available": easy,
                "detail": "Inclus avec flowMD. Arabe + français impossible simultanément.",
            },
            {
                "id": "tesseract",
                "label": "Tesseract",
                "available": tess.available,
                "detail": (
                    f"{tess.version} — langues : {', '.join(sorted(tess.langs)) or 'aucune (fr/ar/en)'}"
                    if tess.available
                    else "Binaire tesseract introuvable (installation facultative)."
                ),
                "langs": sorted(tess.langs),
            },
        ],
        "models_ready": models_ready(settings),
        "docling_installed": docling_available(),
    }
