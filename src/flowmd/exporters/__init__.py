"""Exports MD / DOCX / XLSX depuis un DoclingDocument."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .docx import export_docx
from .markdown import export_markdown
from .xlsx import export_xlsx

SUPPORTED_FORMATS = ("md", "docx", "xlsx")


def normalize_formats(formats: str | list[str] | None) -> list[str]:
    if formats is None:
        return list(SUPPORTED_FORMATS)
    if isinstance(formats, str):
        items = [part.strip().lower() for part in formats.replace(";", ",").split(",")]
    else:
        items = [str(part).strip().lower() for part in formats]
    items = [item for item in items if item]
    if not items:
        return list(SUPPORTED_FORMATS)
    result: list[str] = []
    for item in items:
        fmt = {"markdown": "md", "word": "docx", "excel": "xlsx"}.get(item, item)
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Format inconnu : « {item} ». Formats pris en charge : md, docx, xlsx."
            )
        if fmt not in result:
            result.append(fmt)
    return result


def export_all(
    document: Any,
    formats: list[str],
    out_dir: Path,
    stem: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Path], list[dict[str, str]]]:
    """Exporte le document dans chaque format demandé.

    Retourne (chemins par format, avertissements). Le Markdown est toujours
    produit en premier car l'export DOCX en dépend.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    warnings: list[dict[str, str]] = []

    md_path = export_markdown(document, out_dir, stem)
    if "md" in formats:
        outputs["md"] = md_path

    if "docx" in formats:
        docx_path, docx_warnings = export_docx(md_path, out_dir, stem)
        outputs["docx"] = docx_path
        warnings.extend(docx_warnings)

    if "xlsx" in formats:
        outputs["xlsx"] = export_xlsx(document, out_dir / f"{stem}.xlsx", metadata or {})

    return outputs, warnings
