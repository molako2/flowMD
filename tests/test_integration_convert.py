"""Tests d'intégration lents : vraie conversion Docling sur les échantillons.

Exécution : pytest -m integration
Prérequis : docling installé et modèles téléchargés (flowmd setup).
"""

from pathlib import Path

import pytest

from flowmd.config import Settings
from flowmd.engines import docling_available, probe_tesseract
from flowmd.exporters import export_all
from flowmd.languages import normalize_langs, plan_ocr

SAMPLES = Path(__file__).parent / "samples"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not docling_available(), reason="docling non installé"),
    pytest.mark.timeout(1800),
]


@pytest.fixture(scope="module")
def settings(tmp_path_factory):
    data_dir = Path("data")
    if not data_dir.is_dir():
        data_dir = tmp_path_factory.mktemp("data")
    return Settings(data_dir=data_dir)


def _convert(settings: Settings, pdf: Path, langs: str, out: Path, force_ocr: bool = False):
    from flowmd.pipeline import convert_pdf

    tess = probe_tesseract()
    plan = plan_ocr("auto", normalize_langs(langs), tess.available, tess.langs)
    result = convert_pdf(pdf, plan, settings, force_ocr=force_ocr)
    outputs, warnings = export_all(
        result.document,
        ["md", "docx", "xlsx"],
        out,
        pdf.stem,
        {"source": pdf.name, "engine": plan.engine, "langs": plan.langs, "pages": result.page_count},
    )
    return outputs, result


def test_french_invoice_with_table(settings, tmp_path):
    outputs, _ = _convert(settings, SAMPLES / "fr_facture.pdf", "fr,en", tmp_path)
    md = outputs["md"].read_text(encoding="utf-8")
    assert "FACTURE" in md
    assert "Audit" in md

    import openpyxl

    wb = openpyxl.load_workbook(outputs["xlsx"])
    assert any(name.startswith("Tableau_") for name in wb.sheetnames), (
        "le tableau de la facture doit être détecté"
    )


def test_english_table(settings, tmp_path):
    outputs, _ = _convert(settings, SAMPLES / "en_table.pdf", "en", tmp_path)
    md = outputs["md"].read_text(encoding="utf-8")
    assert "QUARTERLY" in md or "Quarterly" in md


def test_arabic_scanned_document(settings, tmp_path):
    """Test critique : OCR d'un document arabe scanné (image seule)."""
    outputs, result = _convert(
        settings, SAMPLES / "ar_scan.pdf", "ar,en", tmp_path, force_ocr=True
    )
    md = outputs["md"].read_text(encoding="utf-8")
    truth_words = set((SAMPLES / "ar_scan.txt").read_text(encoding="utf-8").split())
    found = sum(1 for word in truth_words if word in md)
    # Au moins un tiers des mots de la vérité terrain doit être reconnu.
    assert found >= len(truth_words) / 3, (
        f"OCR arabe trop faible : {found}/{len(truth_words)} mots reconnus.\n{md[:500]}"
    )
    assert outputs["docx"].is_file()
