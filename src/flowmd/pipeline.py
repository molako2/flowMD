"""Cœur de conversion : PDF → DoclingDocument.

Les imports Docling sont paresseux : les tests unitaires et le CLI de base
fonctionnent sans que les modèles (ni docling) soient installés.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Settings
from .engines import build_ocr_options, models_ready
from .languages import OcrPlan


@dataclass(frozen=True)
class ConversionConfig:
    """Clé de cache d'un convertisseur Docling."""

    engine: str
    langs: tuple[str, ...]
    force_ocr: bool = False


@dataclass
class ConversionOutput:
    document: Any  # DoclingDocument
    page_count: int
    warnings: list[dict[str, str]] = field(default_factory=list)


_converter_cache: dict[ConversionConfig, Any] = {}
_cache_lock = threading.Lock()


def count_pages(pdf_path: Path) -> int:
    """Nombre de pages via pypdfium2 (dépendance de docling), 0 si illisible."""
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(pdf_path))
        try:
            return len(pdf)
        finally:
            pdf.close()
    except Exception:
        return 0


def _build_converter(cfg: ConversionConfig, plan: OcrPlan, settings: Settings):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.generate_picture_images = True
    pipeline_options.images_scale = 2.0
    pipeline_options.ocr_options = build_ocr_options(plan, settings, force_ocr=cfg.force_ocr)

    # Le moteur PaddleOCR est fourni par flowMD via le système de plugins Docling.
    if cfg.engine == "paddleocr":
        pipeline_options.allow_external_plugins = True

    # N'imposer artifacts_path que si les modèles y ont déjà été téléchargés,
    # sinon Docling utilise/alimente son cache par défaut à la demande.
    if models_ready(settings):
        pipeline_options.artifacts_path = settings.docling_artifacts_dir

    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )


def get_converter(cfg: ConversionConfig, plan: OcrPlan, settings: Settings):
    """Convertisseur mis en cache par configuration (chargement des modèles coûteux)."""
    with _cache_lock:
        converter = _converter_cache.get(cfg)
        if converter is None:
            converter = _build_converter(cfg, plan, settings)
            _converter_cache[cfg] = converter
        return converter


def clear_converter_cache() -> None:
    with _cache_lock:
        _converter_cache.clear()


def convert_pdf(pdf_path: Path, plan: OcrPlan, settings: Settings, force_ocr: bool = False) -> ConversionOutput:
    """Convertit un PDF en DoclingDocument selon le plan OCR donné."""
    cfg = ConversionConfig(engine=plan.engine, langs=tuple(plan.langs), force_ocr=force_ocr)
    pages = count_pages(pdf_path)
    warnings = list(plan.warnings)
    if pages > settings.page_warning_threshold:
        warnings.append(
            {
                "code": "LARGE_DOCUMENT",
                "message": (
                    f"Document volumineux ({pages} pages) : le traitement sur CPU "
                    "peut prendre plusieurs minutes."
                ),
            }
        )

    converter = get_converter(cfg, plan, settings)
    result = converter.convert(str(pdf_path))

    from docling.datamodel.base_models import ConversionStatus

    if result.status not in (ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS):
        raise RuntimeError(f"Échec de la conversion Docling : {result.status}")
    if result.status == ConversionStatus.PARTIAL_SUCCESS:
        warnings.append(
            {
                "code": "PARTIAL_CONVERSION",
                "message": "Conversion partielle : certaines pages n'ont pas pu être traitées.",
            }
        )

    return ConversionOutput(document=result.document, page_count=pages, warnings=warnings)
