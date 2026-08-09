"""Tests du plugin Docling PaddleOCR (sans modèles ni téléchargement)."""

import pytest

pytest.importorskip("docling", reason="docling requis pour le plugin PaddleOCR")

from docling.datamodel.accelerator_options import AcceleratorOptions  # noqa: E402

from flowmd.ocr_paddle import (  # noqa: E402
    PaddleOcrModel,
    PaddleOcrOptions,
    ocr_engines,
)


class TestPluginContract:
    def test_kind(self):
        assert PaddleOcrOptions.kind == "paddleocr"

    def test_options_type(self):
        assert PaddleOcrModel.get_options_type() is PaddleOcrOptions

    def test_entry_point_function(self):
        engines = ocr_engines()
        assert PaddleOcrModel in engines["ocr_engines"]

    def test_mkldnn_default_is_auto(self):
        assert PaddleOcrOptions(lang=["fr"]).enable_mkldnn is None

    def test_disabled_model_needs_no_paddle(self):
        model = PaddleOcrModel(
            enabled=False,
            artifacts_path=None,
            options=PaddleOcrOptions(lang=["fr"]),
            accelerator_options=AcceleratorOptions(),
        )
        assert not model.enabled

    def test_registered_in_docling_factory(self):
        from docling.models.factories import get_ocr_factory

        factory = get_ocr_factory(allow_external_plugins=True)
        assert "paddleocr" in set(factory.registered_kind)


class TestResultParsing:
    def test_poly_bounds(self):
        poly = [(10, 20), (110, 22), (108, 60), (12, 58)]
        assert PaddleOcrModel._poly_bounds(poly) == (10.0, 20.0, 110.0, 60.0)

    def test_iter_lines_rec_polys(self):
        res = {
            "rec_texts": ["Facture", "تقرير"],
            "rec_scores": [0.98, 0.91],
            "rec_polys": [
                [(0, 0), (50, 0), (50, 10), (0, 10)],
                [(0, 20), (50, 20), (50, 30), (0, 30)],
            ],
        }
        lines = list(PaddleOcrModel._iter_lines(res))
        assert [text for text, _, _ in lines] == ["Facture", "تقرير"]

    def test_iter_lines_dt_polys_fallback(self):
        res = {
            "rec_texts": ["Total"],
            "rec_scores": [0.8],
            "rec_polys": None,
            "dt_polys": [[(0, 0), (10, 0), (10, 5), (0, 5)]],
        }
        lines = list(PaddleOcrModel._iter_lines(res))
        assert lines[0][0] == "Total"

    def test_iter_lines_bad_result(self):
        assert list(PaddleOcrModel._iter_lines(None)) == []
        assert list(PaddleOcrModel._iter_lines({"autre": 1})) == []
