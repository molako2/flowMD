"""Tests des règles de langues et de compatibilité moteur (D1)."""

import pytest

from flowmd.languages import (
    LanguageError,
    easyocr_supports,
    normalize_langs,
    plan_ocr,
)


class TestNormalizeLangs:
    def test_string_with_aliases(self):
        assert normalize_langs("fra,ara,eng") == ["fr", "ar", "en"]
        assert normalize_langs("français, arabe") == ["fr", "ar"]
        assert normalize_langs("FR;EN") == ["fr", "en"]

    def test_deduplication_preserves_order(self):
        assert normalize_langs(["ar", "fr", "ar"]) == ["ar", "fr"]

    def test_empty_defaults_to_all(self):
        assert normalize_langs(None) == ["fr", "ar", "en"]
        assert normalize_langs("") == ["fr", "ar", "en"]
        assert normalize_langs([]) == ["fr", "ar", "en"]

    def test_unknown_language_raises(self):
        with pytest.raises(LanguageError, match="inconnue"):
            normalize_langs("de")


class TestEasyocrSupports:
    def test_ar_fr_incompatible(self):
        assert not easyocr_supports(["ar", "fr"])
        assert not easyocr_supports(["fr", "ar", "en"])

    def test_valid_combinations(self):
        assert easyocr_supports(["ar", "en"])
        assert easyocr_supports(["fr", "en"])
        assert easyocr_supports(["ar"])
        assert easyocr_supports(["fr"])


class TestPlanOcr:
    def test_easyocr_simple(self):
        plan = plan_ocr("easyocr", ["fr", "en"], tesseract_available=False)
        assert plan.engine == "easyocr"
        assert plan.langs == ["fr", "en"]
        assert plan.engine_lang_codes == ["fr", "en"]
        assert plan.warnings == []

    def test_easyocr_ar_fr_switches_to_tesseract(self):
        plan = plan_ocr("easyocr", ["ar", "fr"], tesseract_available=True)
        assert plan.engine == "tesseract"
        assert plan.langs == ["ar", "fr"]
        assert plan.warnings[0]["code"] == "EASYOCR_AR_FR_SWITCHED_TESSERACT"

    def test_easyocr_ar_fr_drops_fr_without_tesseract(self):
        plan = plan_ocr("easyocr", ["ar", "fr", "en"], tesseract_available=False)
        assert plan.engine == "easyocr"
        assert plan.langs == ["ar", "en"]
        assert plan.warnings[0]["code"] == "EASYOCR_AR_FR_DROPPED_FR"

    def test_auto_prefers_tesseract_for_arabic(self):
        plan = plan_ocr("auto", ["ar", "fr", "en"], tesseract_available=True)
        assert plan.engine == "tesseract"
        assert plan.warnings == []

    def test_auto_uses_easyocr_when_no_tesseract(self):
        plan = plan_ocr("auto", ["fr", "en"], tesseract_available=False)
        assert plan.engine == "easyocr"

    def test_auto_falls_back_when_tesseract_missing_langs(self):
        plan = plan_ocr(
            "auto", ["ar", "fr"], tesseract_available=True, tesseract_langs={"en"}
        )
        # Tesseract inutilisable (ara/fra absents) → EasyOCR + abandon du fr
        assert plan.engine == "easyocr"
        assert plan.langs == ["ar"]
        assert plan.warnings[0]["code"] == "EASYOCR_AR_FR_DROPPED_FR"

    def test_tesseract_explicit_missing_binary_raises(self):
        with pytest.raises(LanguageError, match="Tesseract"):
            plan_ocr("tesseract", ["fr"], tesseract_available=False)

    def test_tesseract_explicit_missing_langs_raises(self):
        with pytest.raises(LanguageError, match="manquantes"):
            plan_ocr("tesseract", ["ar"], tesseract_available=True, tesseract_langs={"fr", "en"})

    def test_tesseract_lang_codes(self):
        plan = plan_ocr("tesseract", ["fr", "ar", "en"], tesseract_available=True)
        assert plan.engine_lang_codes == ["fra", "ara", "eng"]

    def test_unknown_engine_raises(self):
        with pytest.raises(LanguageError, match="Moteur"):
            plan_ocr("paddle", ["fr"], tesseract_available=False)
