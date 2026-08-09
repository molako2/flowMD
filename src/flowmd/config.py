"""Configuration de flowMD (variables d'environnement préfixées FLOWMD_)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLOWMD_", env_file=".env", extra="ignore")

    # Répertoire racine des données (uploads, sorties, modèles)
    data_dir: Path = Path("data")

    # Limites d'upload
    max_upload_mb: int = 200
    max_batch_mb: int = 500

    # Durée de vie des jobs terminés (nettoyage automatique)
    job_ttl_hours: int = 24

    # Serveur
    host: str = "127.0.0.1"
    port: int = 8000

    # OCR
    default_engine: str = "auto"  # auto | easyocr | tesseract | paddleocr
    easyocr_gpu: bool = False

    # Chemin complet de tesseract(.exe) si le binaire n'est pas dans le PATH
    # (variable d'environnement FLOWMD_TESSERACT_CMD)
    tesseract_cmd: str | None = None

    # Avertir au-delà de ce nombre de pages (durée de traitement sur CPU)
    page_warning_threshold: int = 300

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @property
    def docling_artifacts_dir(self) -> Path:
        return self.models_dir / "docling"

    @property
    def easyocr_models_dir(self) -> Path:
        return self.models_dir / "easyocr"

    def ensure_dirs(self) -> None:
        for d in (self.uploads_dir, self.outputs_dir, self.models_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
