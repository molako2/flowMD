"""Moteur OCR PaddleOCR (PP-OCRv6) — plugin Docling.

PaddleOCR charge un seul modèle de reconnaissance à la fois :
- ``fr`` / ``en`` → modèle unifié PP-OCRv6 (50 langues, latin inclus) ;
- ``ar`` → modèle arabe (PP-OCRv5, repli automatique de PaddleOCR).

Arabe + français simultanés restent donc impossibles (voir languages.plan_ocr).

Le module est enregistré comme plugin Docling via l'entry point ``docling``
(fonction :func:`ocr_engines`) et activé par
``pipeline_options.allow_external_plugins = True``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar, Literal

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import Page
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import OcrOptions
from docling.datamodel.settings import settings as docling_settings
from docling.models.base_ocr_model import BaseOcrModel
from docling.utils.accelerator_utils import decide_device
from docling.utils.profiling import TimeRecorder

_log = logging.getLogger(__name__)

INSTALL_HINT = (
    "PaddleOCR n'est pas installé. Installez-le avec "
    "« pip install paddlepaddle paddleocr » (ou pip install -e \".[paddleocr]\")."
)


class PaddleOcrOptions(OcrOptions):
    """Options du moteur PaddleOCR (PP-OCRv6)."""

    kind: ClassVar[Literal["paddleocr"]] = "paddleocr"

    # PaddleOCR ne charge qu'un modèle de reconnaissance : seul le premier
    # code de la liste est utilisé (fr | ar | en).
    lang: list[str] = ["fr"]

    # None = choix automatique par PaddleOCR (PP-OCRv6 quand la langue est
    # prise en charge, PP-OCRv5 en repli, p. ex. pour l'arabe).
    ocr_version: str | None = None

    confidence_threshold: float = 0.5
    use_textline_orientation: bool = True


class PaddleOcrModel(BaseOcrModel):
    """Adaptateur Docling → API pipeline de PaddleOCR 3.x."""

    def __init__(
        self,
        enabled: bool,
        artifacts_path: Path | None,
        options: PaddleOcrOptions,
        accelerator_options: AcceleratorOptions,
    ):
        super().__init__(
            enabled=enabled,
            artifacts_path=artifacts_path,
            options=options,
            accelerator_options=accelerator_options,
        )
        self.options: PaddleOcrOptions
        self.scale = self.options.scale

        if self.enabled:
            try:
                from paddleocr import PaddleOCR
            except ImportError as exc:
                raise ImportError(INSTALL_HINT) from exc

            device = decide_device(accelerator_options.device)
            paddle_device = "gpu" if device.startswith("cuda") else "cpu"

            kwargs: dict = {
                "lang": self.options.lang[0] if self.options.lang else "fr",
                "device": paddle_device,
                # Étapes de pré-traitement documentaire inutiles ici : Docling
                # fournit déjà des zones de page correctement orientées.
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": self.options.use_textline_orientation,
            }
            if self.options.ocr_version:
                kwargs["ocr_version"] = self.options.ocr_version
            self.reader = PaddleOCR(**kwargs)

    def __call__(
        self, conv_res: ConversionResult, page_batch: Iterable[Page]
    ) -> Iterable[Page]:
        import numpy
        from docling_core.types.doc import BoundingBox, CoordOrigin
        from docling_core.types.doc.page import BoundingRectangle, TextCell

        if not self.enabled:
            yield from page_batch
            return

        for page in page_batch:
            assert page._backend is not None
            if not page._backend.is_valid():
                yield page
                continue

            with TimeRecorder(conv_res, "ocr"):
                ocr_rects = self.get_ocr_rects(page)

                all_ocr_cells: list[TextCell] = []
                for ocr_rect in ocr_rects:
                    if ocr_rect.area() == 0:
                        continue
                    high_res_image = page._backend.get_page_image(
                        scale=self.scale, cropbox=ocr_rect
                    )
                    # PIL fournit du RVB ; PaddleOCR attend du BGR (format cv2).
                    im = numpy.array(high_res_image)[:, :, ::-1]
                    del high_res_image

                    try:
                        results = self.reader.predict(im)
                    finally:
                        del im

                    index = len(all_ocr_cells)
                    for res in results or []:
                        for text, score, poly in self._iter_lines(res):
                            if score < self.options.confidence_threshold or not text:
                                continue
                            left, top, right, bottom = self._poly_bounds(poly)
                            all_ocr_cells.append(
                                TextCell(
                                    index=index,
                                    text=text,
                                    orig=text,
                                    from_ocr=True,
                                    confidence=float(score),
                                    rect=BoundingRectangle.from_bounding_box(
                                        BoundingBox.from_tuple(
                                            coord=(
                                                (left / self.scale) + ocr_rect.l,
                                                (top / self.scale) + ocr_rect.t,
                                                (right / self.scale) + ocr_rect.l,
                                                (bottom / self.scale) + ocr_rect.t,
                                            ),
                                            origin=CoordOrigin.TOPLEFT,
                                        )
                                    ),
                                )
                            )
                            index += 1

                self.post_process_cells(all_ocr_cells, page, conv_res)

            if docling_settings.debug.visualize_ocr:
                self.draw_ocr_rects_and_cells(conv_res, page, ocr_rects)

            yield page

    @staticmethod
    def _iter_lines(res) -> Iterable[tuple[str, float, object]]:
        """Extrait (texte, score, polygone) d'un résultat PaddleOCR 3.x."""
        try:
            texts = res["rec_texts"]
            scores = res["rec_scores"]
            polys = res.get("rec_polys")
            if polys is None:
                polys = res.get("dt_polys")
        except (TypeError, KeyError):
            return
        if polys is None:
            return
        yield from zip(texts, scores, polys, strict=False)

    @staticmethod
    def _poly_bounds(poly) -> tuple[float, float, float, float]:
        xs = [float(point[0]) for point in poly]
        ys = [float(point[1]) for point in poly]
        return min(xs), min(ys), max(xs), max(ys)

    @classmethod
    def get_options_type(cls) -> type[OcrOptions]:
        return PaddleOcrOptions


def ocr_engines() -> dict:
    """Point d'entrée plugin Docling (groupe « docling »)."""
    return {"ocr_engines": [PaddleOcrModel]}
