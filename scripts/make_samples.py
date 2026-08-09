"""Génère les PDF d'exemple committés dans tests/samples/.

- fr_facture.pdf : facture française avec tableau (couche texte)
- en_table.pdf   : document anglais avec tableau (couche texte)
- ar_scan.pdf    : document arabe « scanné » (image seule, sans couche texte)

Usage : python scripts/make_samples.py
Dépendances : fpdf2, uharfbuzz (façonnage arabe), pypdfium2, pillow.
Police : tests/assets/fonts/NotoNaskhArabic-Regular.ttf (licence OFL).
"""

from __future__ import annotations

import io
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "tests" / "samples"
FONTS = ROOT / "tests" / "assets" / "fonts"

AR_FONT = FONTS / "NotoNaskhArabic-Regular.ttf"

FR_LINES = [
    "FACTURE N° 2026-0142",
    "Société Exemple SARL - Casablanca",
    "Date : 15 janvier 2026",
    "",
    "Détail des prestations :",
]
FR_TABLE = [
    ["Désignation", "Quantité", "Prix unitaire (MAD)", "Total (MAD)"],
    ["Audit des comptes annuels", "1", "25 000,00", "25 000,00"],
    ["Revue fiscale trimestrielle", "4", "6 500,00", "26 000,00"],
    ["Formation équipe comptable", "2", "3 200,00", "6 400,00"],
]
FR_FOOTER = ["Total hors taxes : 57 400,00 MAD", "TVA (20 %) : 11 480,00 MAD", "Total TTC : 68 880,00 MAD"]

EN_LINES = [
    "QUARTERLY FINANCIAL SUMMARY",
    "Example Company Ltd - Fiscal year 2026",
    "",
    "Key figures by quarter:",
]
EN_TABLE = [
    ["Quarter", "Revenue (USD)", "Expenses (USD)", "Net income (USD)"],
    ["Q1 2026", "120,500", "84,300", "36,200"],
    ["Q2 2026", "134,900", "90,150", "44,750"],
    ["Q3 2026", "128,400", "88,700", "39,700"],
]
EN_FOOTER = ["Total net income (9 months): 120,650 USD", "Prepared by the finance department."]

AR_LINES = [
    "تقرير مالي سنوي",
    "شركة المثال للمحاسبة والتدقيق",
    "السنة المالية 2026",
    "",
    "ملخص النتائج:",
    "بلغ إجمالي الإيرادات خمسة ملايين درهم خلال هذه السنة.",
    "ارتفعت الأرباح الصافية بنسبة اثني عشر في المائة مقارنة بالسنة الماضية.",
    "يوصي مجلس الإدارة بتوزيع أرباح على المساهمين.",
]


def _simple_pdf(lines: list[str], table: list[list[str]] | None, footer: list[str]) -> FPDF:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.set_font_size(16)
    pdf.cell(0, 10, lines[0], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font_size(12)
    for line in lines[1:]:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    if table:
        pdf.ln(2)
        with pdf.table(width=180, col_widths=(70, 30, 40, 40)) as t:
            for row_data in table:
                row = t.row()
                for cell in row_data:
                    row.cell(cell)
        pdf.ln(4)
    for line in footer:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    return pdf


def make_fr() -> None:
    pdf = _simple_pdf(FR_LINES, FR_TABLE, FR_FOOTER)
    pdf.output(str(SAMPLES / "fr_facture.pdf"))
    truth = FR_LINES + [" ".join(r) for r in FR_TABLE] + FR_FOOTER
    (SAMPLES / "fr_facture.txt").write_text("\n".join(t for t in truth if t), encoding="utf-8")


def make_en() -> None:
    pdf = _simple_pdf(EN_LINES, EN_TABLE, EN_FOOTER)
    pdf.output(str(SAMPLES / "en_table.pdf"))
    truth = EN_LINES + [" ".join(r) for r in EN_TABLE] + EN_FOOTER
    (SAMPLES / "en_table.txt").write_text("\n".join(t for t in truth if t), encoding="utf-8")


def make_ar() -> None:
    if not AR_FONT.is_file():
        raise SystemExit(f"Police arabe manquante : {AR_FONT}")

    # 1) PDF texte avec façonnage HarfBuzz (lettres liées, ordre RTL correct)
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("noto-ar", fname=str(AR_FONT))
    pdf.set_font("noto-ar", size=16)
    pdf.set_text_shaping(True)
    for line in AR_LINES:
        if line:
            pdf.cell(0, 12, line, new_x="LMARGIN", new_y="NEXT", align="R")
        else:
            pdf.ln(6)
    text_pdf_bytes = bytes(pdf.output())

    # 2) Rasterisation → PDF image seule (simule un document scanné)
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(text_pdf_bytes)
    page = doc[0]
    image = page.render(scale=200 / 72).to_pil()  # ~200 DPI
    doc.close()

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    scan = FPDF(unit="pt", format=(image.width * 72 / 200, image.height * 72 / 200))
    scan.add_page()
    scan.image(buffer, x=0, y=0, w=scan.w, h=scan.h)
    scan.output(str(SAMPLES / "ar_scan.pdf"))

    (SAMPLES / "ar_scan.txt").write_text(
        "\n".join(line for line in AR_LINES if line), encoding="utf-8"
    )


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    make_fr()
    make_en()
    make_ar()
    for f in sorted(SAMPLES.iterdir()):
        print(f"  {f.name} ({f.stat().st_size} octets)")


if __name__ == "__main__":
    main()
