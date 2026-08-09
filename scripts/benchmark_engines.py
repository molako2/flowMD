"""Benchmark des moteurs OCR (EasyOCR vs Tesseract) sur les échantillons fr/ar/en.

Compare, pour chaque moteur disponible et chaque échantillon :
- le temps de conversion (OCR pleine page forcé) ;
- la similarité du texte extrait avec la vérité terrain (rapidfuzz, 0-100).

Usage : python scripts/benchmark_engines.py
Prérequis : docling installé, modèles téléchargés (flowmd setup).
Le tableau produit est destiné au README (section « Benchmark »).
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "tests" / "samples"
sys.path.insert(0, str(ROOT / "src"))

from flowmd.config import Settings  # noqa: E402
from flowmd.engines import (  # noqa: E402
    docling_available,
    paddleocr_available,
    probe_tesseract,
)
from flowmd.languages import normalize_langs, plan_ocr  # noqa: E402

CASES = [
    ("fr_facture.pdf", "fr_facture.txt", "fr,en", "Français (facture, couche texte)"),
    ("en_table.pdf", "en_table.txt", "en", "Anglais (tableau, couche texte)"),
    ("ar_scan.pdf", "ar_scan.txt", "ar,en", "Arabe (document scanné)"),
]

_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    text = re.sub(r"[|#*_`\-]+", " ", text)
    return _WS.sub(" ", text).strip().lower()


def main() -> None:
    if not docling_available():
        raise SystemExit("docling n'est pas installé : pip install -e .")

    from rapidfuzz import fuzz

    from flowmd.pipeline import clear_converter_cache, convert_pdf

    settings = Settings()
    tess = probe_tesseract()
    paddle = paddleocr_available()
    engines = ["easyocr"]
    if paddle:
        engines.append("paddleocr")
    else:
        print("Note : PaddleOCR non installé (pip install paddlepaddle paddleocr) — ignoré.\n")
    if tess.available and {"fr", "ar", "en"} <= tess.langs:
        engines.append("tesseract")
    else:
        print("Note : Tesseract absent ou données ara/fra/eng manquantes — ignoré.\n")

    rows: list[tuple[str, str, str, str]] = []
    for engine in engines:
        for pdf_name, truth_name, langs, label in CASES:
            plan = plan_ocr(
                engine,
                normalize_langs(langs),
                tess.available,
                tess.langs,
                paddleocr_available=paddle,
            )
            if plan.engine != engine:
                rows.append((label, engine, "—", "non pris en charge (ar+fr)"))
                continue
            effective_note = "" if plan.langs == normalize_langs(langs) else (
                f" (langues : {','.join(plan.langs)})"
            )
            print(f"[{engine}] {pdf_name} …", flush=True)
            start = time.perf_counter()
            try:
                result = convert_pdf(
                    SAMPLES / pdf_name, plan, settings, force_ocr=True
                )
                elapsed = time.perf_counter() - start
                extracted = _normalize(result.document.export_to_markdown())
                truth = _normalize((SAMPLES / truth_name).read_text(encoding="utf-8"))
                score = fuzz.token_set_ratio(extracted, truth)
                rows.append((label, engine, f"{elapsed:.1f} s", f"{score:.0f} / 100{effective_note}"))
            except Exception as exc:
                rows.append((label, engine, "—", f"échec : {exc}"))
        clear_converter_cache()

    print("\n| Échantillon | Moteur | Temps | Similarité vérité terrain |")
    print("|---|---|---|---|")
    for label, engine, elapsed, score in rows:
        print(f"| {label} | {engine} | {elapsed} | {score} |")


if __name__ == "__main__":
    main()
