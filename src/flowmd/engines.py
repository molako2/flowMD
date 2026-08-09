"""Détection des moteurs OCR disponibles et fabrique des options Docling."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .config import Settings, get_settings
from .languages import _TESSERACT_CODES, OcrPlan  # noqa: PLC2701

_TESS_PUBLIC_BY_CODE = {v: k for k, v in _TESSERACT_CODES.items()}


@dataclass
class TesseractInfo:
    available: bool
    cmd: str | None = None
    version: str | None = None
    langs: set[str] = field(default_factory=set)  # codes publics fr/ar/en
    tessdata_dir: str | None = None  # dossier de langues imposé (--tessdata-dir)


def _candidate_tesseract_cmds() -> list[str]:
    """Emplacements possibles du binaire tesseract, par ordre de priorité.

    L'installateur Windows (UB-Mannheim) n'ajoute pas tesseract.exe au PATH
    par défaut : on sonde donc aussi les dossiers d'installation standards.
    """
    candidates: list[str] = []

    configured = get_settings().tesseract_cmd
    if configured:
        candidates.append(configured)

    which = shutil.which("tesseract")
    if which:
        candidates.append(which)

    # Installation « portable » à côté de flowMD (ex. C:\flowMD\Tesseract-OCR) :
    # sondée depuis le dossier courant (start.bat/start.sh) ET depuis la racine
    # du projet (installation éditable), pour être indépendant du cwd.
    exe_name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
    project_root = Path(__file__).resolve().parents[2]
    for base in (Path.cwd(), project_root):
        portable = base / "Tesseract-OCR" / exe_name
        if portable.is_file():
            candidates.append(str(portable))

    if sys.platform == "win32":
        roots = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
        ]
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            roots.append(str(Path(local_appdata) / "Programs"))
        for root in roots:
            if not root:
                continue
            exe = Path(root) / "Tesseract-OCR" / "tesseract.exe"
            if exe.is_file():
                candidates.append(str(exe))

    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def _probe_tesseract_cmd(cmd: str) -> TesseractInfo:
    """Interroge un binaire tesseract donné.

    Si un dossier ``tessdata`` existe à côté du binaire, il est imposé via
    ``--tessdata-dir`` : une variable TESSDATA_PREFIX parasite (reste d'une
    ancienne installation) ne peut alors plus détourner les langues.
    """
    tessdata_dir: str | None = None
    sidecar = Path(cmd).parent / "tessdata"
    if sidecar.is_dir():
        tessdata_dir = str(sidecar)
    tessdata_args = ["--tessdata-dir", tessdata_dir] if tessdata_dir else []

    try:
        version_out = subprocess.run(
            [cmd, "--version"], capture_output=True, text=True, timeout=10
        )
        version = version_out.stdout.splitlines()[0].strip() if version_out.stdout else None
        langs_out = subprocess.run(
            [cmd, *tessdata_args, "--list-langs"], capture_output=True, text=True, timeout=10
        )
        installed = {
            line.strip()
            for line in langs_out.stdout.splitlines()
            if line.strip() and not line.lower().startswith("list of")
        }
        public = {_TESS_PUBLIC_BY_CODE[code] for code in installed if code in _TESS_PUBLIC_BY_CODE}
        return TesseractInfo(
            available=True, cmd=cmd, version=version, langs=public, tessdata_dir=tessdata_dir
        )
    except (OSError, subprocess.SubprocessError):
        return TesseractInfo(available=False)


def probe_tesseract() -> TesseractInfo:
    """Cherche le binaire tesseract (PATH + emplacements Windows) et ses langues."""
    for cmd in _candidate_tesseract_cmds():
        info = _probe_tesseract_cmd(cmd)
        if info.available:
            return info
    return TesseractInfo(available=False)


def easyocr_available() -> bool:
    return importlib.util.find_spec("easyocr") is not None


def paddleocr_available() -> bool:
    return importlib.util.find_spec("paddleocr") is not None


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

        options = TesseractCliOcrOptions(
            lang=plan.engine_lang_codes,
            force_full_page_ocr=force_ocr,
        )
        # Hors PATH (cas Windows typique) : transmettre le chemin détecté,
        # et imposer le dossier de langues du binaire (--tessdata-dir) pour
        # neutraliser un éventuel TESSDATA_PREFIX parasite.
        tess = probe_tesseract()
        if tess.cmd:
            options.tesseract_cmd = tess.cmd
        if tess.tessdata_dir:
            options.path = tess.tessdata_dir
        return options

    if plan.engine == "paddleocr":
        from .ocr_paddle import PaddleOcrOptions

        return PaddleOcrOptions(
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
    paddle = paddleocr_available()
    return {
        "engines": [
            {
                "id": "auto",
                "label": "Automatique (recommandé)",
                "available": easy or tess.available or paddle,
                "detail": "Choisit le meilleur moteur selon les langues demandées.",
            },
            {
                "id": "paddleocr",
                "label": "PaddleOCR (PP-OCRv6)",
                "available": paddle,
                "detail": (
                    "Le plus précis (PP-OCRv6, arabe via PP-OCRv5). "
                    "Arabe + français impossible simultanément."
                    if paddle
                    else "Non installé : pip install paddlepaddle paddleocr"
                ),
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
                    f"{tess.version} — langues fr/ar/en : {', '.join(sorted(tess.langs)) or 'AUCUNE (réinstallez avec Arabic + French)'}"
                    if tess.available
                    else (
                        "Introuvable. Si Tesseract vient d'être installé, fermez et "
                        "relancez flowMD (start.bat). Sinon, définissez "
                        "FLOWMD_TESSERACT_CMD=chemin\\vers\\tesseract.exe."
                    )
                ),
                "langs": sorted(tess.langs),
            },
        ],
        "models_ready": models_ready(settings),
        "docling_installed": docling_available(),
    }
