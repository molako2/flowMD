"""Fixtures : faux documents Docling pour tester sans modèles ni téléchargement."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

SAMPLES = Path(__file__).parent / "samples"


class FakeProv:
    def __init__(self, page_no: int):
        self.page_no = page_no


class FakeTable:
    def __init__(self, df: pd.DataFrame, page_no: int = 1):
        self._df = df
        self.prov = [FakeProv(page_no)]

    def export_to_dataframe(self, doc=None):
        return self._df


class FakeDocument:
    """Simule l'interface DoclingDocument utilisée par les exporteurs."""

    def __init__(self, markdown: str, tables: list[FakeTable] | None = None):
        self._markdown = markdown
        self.tables = tables or []

    def export_to_markdown(self) -> str:
        return self._markdown


@pytest.fixture
def fake_document() -> FakeDocument:
    df = pd.DataFrame(
        {
            "Désignation": ["Audit des comptes", "Revue fiscale"],
            "Total (MAD)": ["25 000,00", "26 000,00"],
        }
    )
    markdown = (
        "# FACTURE N° 2026-0142\n\n"
        "Société Exemple SARL - Casablanca\n\n"
        "| Désignation | Total (MAD) |\n|---|---|\n"
        "| Audit des comptes | 25 000,00 |\n| Revue fiscale | 26 000,00 |\n\n"
        "تقرير مالي سنوي\n"
    )
    return FakeDocument(markdown, [FakeTable(df, page_no=1)])


@pytest.fixture
def sample_pdf() -> Path:
    return SAMPLES / "fr_facture.pdf"
