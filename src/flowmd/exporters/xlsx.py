"""Export Excel (.xlsx) : un onglet par tableau détecté + onglet Infos."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def _table_dataframe(table: Any, document: Any):
    """export_to_dataframe selon la version de docling-core (avec ou sans doc=)."""
    try:
        return table.export_to_dataframe(doc=document)
    except TypeError:
        return table.export_to_dataframe()


def _table_page(table: Any) -> int | None:
    try:
        prov = table.prov
        if prov:
            return int(prov[0].page_no)
    except Exception:
        pass
    return None


def export_xlsx(document: Any, out_path: Path, metadata: dict[str, Any]) -> Path:
    import pandas as pd

    tables = list(getattr(document, "tables", []) or [])

    infos_rows: list[tuple[str, Any]] = [
        ("Fichier source", metadata.get("source", "")),
        ("Moteur OCR", metadata.get("engine", "")),
        ("Langues", ", ".join(metadata.get("langs", []))),
        ("Pages", metadata.get("pages", "")),
        ("Tableaux détectés", len(tables)),
        ("Généré le", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Généré par", "flowMD"),
    ]

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        infos = pd.DataFrame(infos_rows, columns=["Champ", "Valeur"])
        infos.to_excel(writer, sheet_name="Infos", index=False)

        if not tables:
            note = pd.DataFrame({"Note": ["Aucun tableau détecté dans ce document."]})
            note.to_excel(writer, sheet_name="Aucun tableau", index=False)
        else:
            summary_rows = []
            for idx, table in enumerate(tables, start=1):
                sheet = f"Tableau_{idx}"[:31]
                page = _table_page(table)
                summary_rows.append((sheet, page if page is not None else ""))
                try:
                    df = _table_dataframe(table, document)
                except Exception:
                    df = pd.DataFrame(
                        {"Erreur": [f"Impossible d'extraire le tableau {idx}."]}
                    )
                df.to_excel(writer, sheet_name=sheet, index=False)
            summary = pd.DataFrame(summary_rows, columns=["Onglet", "Page"])
            summary.to_excel(writer, sheet_name="Infos", index=False, startrow=len(infos_rows) + 3)

    return out_path
