"""Normalisation des langues et règles de compatibilité moteur OCR.

Codes publics : ``fr``, ``ar``, ``en``.

Règle critique (D1) : EasyOCR ne peut pas combiner l'arabe avec une langue
latine autre que l'anglais dans un même lecteur. ``ar + fr`` est donc
impossible avec EasyOCR ; on bascule vers Tesseract s'il est disponible,
sinon on retire le français avec un avertissement explicite.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SUPPORTED_LANGS = ("fr", "ar", "en")

_ALIASES: dict[str, str] = {
    "fr": "fr", "fra": "fr", "fre": "fr", "french": "fr", "francais": "fr", "français": "fr",
    "ar": "ar", "ara": "ar", "arabic": "ar", "arabe": "ar",
    "en": "en", "eng": "en", "english": "en", "anglais": "en",
}

# Codes attendus par chaque moteur
_EASYOCR_CODES = {"fr": "fr", "ar": "ar", "en": "en"}
_TESSERACT_CODES = {"fr": "fra", "ar": "ara", "en": "eng"}
_PADDLE_CODES = {"fr": "fr", "ar": "ar", "en": "en"}

ENGINES = ("auto", "easyocr", "tesseract", "paddleocr")


class LanguageError(ValueError):
    """Langue inconnue ou combinaison invalide."""


def normalize_langs(langs: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalise une liste (ou chaîne ``"fr,ar"``) vers des codes fr/ar/en dédupliqués.

    Une valeur vide retourne les trois langues (fr, ar, en).
    """
    if langs is None:
        return list(SUPPORTED_LANGS)
    if isinstance(langs, str):
        items = [part.strip() for part in langs.replace(";", ",").split(",")]
    else:
        items = [str(part).strip() for part in langs]
    items = [item for item in items if item]
    if not items:
        return list(SUPPORTED_LANGS)

    result: list[str] = []
    for item in items:
        code = _ALIASES.get(item.lower())
        if code is None:
            raise LanguageError(
                f"Langue inconnue : « {item} ». Langues prises en charge : fr, ar, en."
            )
        if code not in result:
            result.append(code)
    return result


def easyocr_supports(langs: list[str]) -> bool:
    """EasyOCR accepte l'arabe uniquement en combinaison avec l'anglais."""
    return not ("ar" in langs and "fr" in langs)


def paddle_supports(langs: list[str]) -> bool:
    """PaddleOCR ne charge qu'un modèle : arabe + français impossible."""
    return not ("ar" in langs and "fr" in langs)


def paddle_primary_lang(langs: list[str]) -> str:
    """Langue effective du modèle PaddleOCR unique (priorité : ar > fr > en)."""
    for lang in ("ar", "fr", "en"):
        if lang in langs:
            return _PADDLE_CODES[lang]
    return "fr"


@dataclass
class OcrPlan:
    """Résultat de la planification OCR : moteur effectif, langues effectives, avertissements."""

    engine: str  # "easyocr" | "tesseract"
    langs: list[str]  # codes publics fr/ar/en réellement utilisés
    warnings: list[dict[str, str]] = field(default_factory=list)

    @property
    def engine_lang_codes(self) -> list[str]:
        if self.engine == "tesseract":
            return [_TESSERACT_CODES[lang] for lang in self.langs]
        if self.engine == "paddleocr":
            # PaddleOCR ne charge qu'un seul modèle de reconnaissance.
            return [paddle_primary_lang(self.langs)]
        return [_EASYOCR_CODES[lang] for lang in self.langs]


def _warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def plan_ocr(
    requested_engine: str,
    langs: list[str],
    tesseract_available: bool,
    tesseract_langs: set[str] | None = None,
    paddleocr_available: bool = False,
) -> OcrPlan:
    """Choisit le moteur et les langues effectives selon les règles de compatibilité.

    ``requested_engine`` : "auto", "easyocr", "tesseract" ou "paddleocr".
    ``tesseract_langs`` : codes publics (fr/ar/en) dont les données Tesseract sont installées.
    """
    langs = normalize_langs(langs)
    engine = (requested_engine or "auto").lower()
    if engine not in ENGINES:
        raise LanguageError(f"Moteur OCR inconnu : « {requested_engine} ».")

    warnings: list[dict[str, str]] = []
    tess_langs = tesseract_langs if tesseract_langs is not None else set(SUPPORTED_LANGS)
    tesseract_usable = tesseract_available and all(lang in tess_langs for lang in langs)
    mixed_ar_fr = "ar" in langs and "fr" in langs

    if engine == "tesseract":
        if not tesseract_available:
            raise LanguageError(
                "Tesseract n'est pas installé (binaire introuvable). "
                "Installez-le ou utilisez le moteur EasyOCR."
            )
        missing = [lang for lang in langs if lang not in tess_langs]
        if missing:
            raise LanguageError(
                "Données de langue Tesseract manquantes pour : "
                + ", ".join(missing)
                + ". Installez les paquets tesseract-ocr correspondants (ara/fra/eng)."
            )
        return OcrPlan(engine="tesseract", langs=langs, warnings=warnings)

    if engine == "paddleocr" and not paddleocr_available:
        raise LanguageError(
            "PaddleOCR n'est pas installé. Installez-le avec "
            "« pip install paddlepaddle paddleocr » puis relancez flowMD."
        )

    if engine == "auto":
        # Seul Tesseract gère arabe + français dans une même passe.
        if mixed_ar_fr and tesseract_usable:
            return OcrPlan(engine="tesseract", langs=langs, warnings=warnings)
        if not mixed_ar_fr:
            # PP-OCRv6 (PaddleOCR) : le plus précis quand il est installé.
            if paddleocr_available:
                return OcrPlan(engine="paddleocr", langs=langs, warnings=warnings)
            if tesseract_usable and "ar" in langs:
                # Tesseract gère bien l'arabe ; préférence auto sans PaddleOCR.
                return OcrPlan(engine="tesseract", langs=langs, warnings=warnings)
            engine = "easyocr"
        else:
            # ar + fr sans Tesseract : moteur mono-passe + abandon du français.
            engine = "paddleocr" if paddleocr_available else "easyocr"

    # engine ∈ {easyocr, paddleocr} — même contrainte : ar + fr impossible.
    supports = easyocr_supports if engine == "easyocr" else paddle_supports
    engine_label = "EasyOCR" if engine == "easyocr" else "PaddleOCR"
    if supports(langs):
        return OcrPlan(engine=engine, langs=langs, warnings=warnings)

    # ar + fr demandés avec un moteur mono-passe
    if tesseract_usable:
        warnings.append(
            _warning(
                "AR_FR_SWITCHED_TESSERACT",
                f"{engine_label} ne prend pas en charge arabe + français simultanément : "
                "le moteur Tesseract a été utilisé à la place.",
            )
        )
        return OcrPlan(engine="tesseract", langs=langs, warnings=warnings)

    effective = [lang for lang in langs if lang != "fr"]
    warnings.append(
        _warning(
            "AR_FR_DROPPED_FR",
            f"{engine_label} ne prend pas en charge arabe + français simultanément et "
            "Tesseract n'est pas disponible : le français a été ignoré pour ce "
            "document (langues utilisées : " + ", ".join(effective) + "). "
            "Installez Tesseract (paquets ara/fra) pour les documents mixtes.",
        )
    )
    return OcrPlan(engine=engine, langs=effective, warnings=warnings)
