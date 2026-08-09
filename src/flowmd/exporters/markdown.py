"""Export Markdown (images extraites référencées à côté du fichier)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_markdown(document: Any, out_dir: Path, stem: str) -> Path:
    out_path = out_dir / f"{stem}.md"
    try:
        from docling_core.types.doc import ImageRefMode

        artifacts_dir = out_dir / f"{stem}_images"
        document.save_as_markdown(
            out_path,
            image_mode=ImageRefMode.REFERENCED,
            artifacts_dir=artifacts_dir,
        )
        # Docling peut créer le dossier même sans image : le retirer s'il est vide.
        if artifacts_dir.is_dir() and not any(artifacts_dir.iterdir()):
            artifacts_dir.rmdir()
    except Exception:
        # Repli robuste : export texte simple (placeholders d'images).
        out_path.write_text(document.export_to_markdown(), encoding="utf-8")
    return out_path
