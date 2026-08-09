"""Interface en ligne de commande flowMD (sortie en français)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer

from . import __version__
from .config import get_settings
from .exporters import normalize_formats
from .languages import LanguageError, normalize_langs, plan_ocr

app = typer.Typer(
    name="flowmd",
    help="Convertisseur local de PDF (OCR) vers Markdown, Word et Excel — fr/ar/en.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"flowMD {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback, is_eager=True,
        help="Affiche la version et quitte.",
    ),
) -> None:
    """flowMD — conversion 100 % locale de vos PDF."""


def _build_plan(engine: str, langs: str):
    from .engines import paddleocr_available, probe_tesseract

    tess = probe_tesseract()
    try:
        return plan_ocr(
            engine,
            normalize_langs(langs),
            tess.available,
            tess.langs,
            paddleocr_available=paddleocr_available(),
        )
    except LanguageError as exc:
        typer.secho(f"Erreur : {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc


@app.command()
def convert(
    files: list[Path] = typer.Argument(..., help="Fichier(s) PDF à convertir."),
    to: str = typer.Option("md,docx,xlsx", "--to", "-t", help="Formats de sortie : md, docx, xlsx."),
    langs: str = typer.Option("fr,ar,en", "--langs", "-l", help="Langues du document : fr, ar, en."),
    engine: str = typer.Option(
        "auto", "--engine", "-e", help="Moteur OCR : auto, easyocr, tesseract, paddleocr."
    ),
    force_ocr: bool = typer.Option(
        False, "--force-ocr", help="Forcer l'OCR complet (documents scannés ou couche texte corrompue)."
    ),
    out: Path = typer.Option(Path("./sorties"), "--out", "-o", help="Dossier de sortie."),
) -> None:
    """Convertit un ou plusieurs PDF en Markdown / Word / Excel."""
    settings = get_settings()
    try:
        formats = normalize_formats(to)
    except ValueError as exc:
        typer.secho(f"Erreur : {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    plan = _build_plan(engine, langs)
    for warning in plan.warnings:
        typer.secho(f"Avertissement : {warning['message']}", fg=typer.colors.YELLOW)

    typer.echo(
        f"Moteur OCR : {plan.engine} — langues : {', '.join(plan.langs)} — "
        f"formats : {', '.join(formats)}"
    )

    from .exporters import export_all
    from .pipeline import convert_pdf

    exit_code = 0
    for pdf in files:
        if not pdf.is_file():
            typer.secho(f"Fichier introuvable : {pdf}", fg=typer.colors.RED, err=True)
            exit_code = 1
            continue
        typer.echo(f"→ Conversion de {pdf.name} …")
        try:
            result = convert_pdf(pdf, plan, settings, force_ocr=force_ocr)
            for warning in result.warnings:
                if warning not in plan.warnings:
                    typer.secho(f"  Avertissement : {warning['message']}", fg=typer.colors.YELLOW)
            stem = pdf.stem or "document"
            metadata = {
                "source": pdf.name,
                "engine": plan.engine,
                "langs": plan.langs,
                "pages": result.page_count,
            }
            outputs, warnings = export_all(result.document, formats, out / stem, stem, metadata)
            for warning in warnings:
                typer.secho(f"  Avertissement : {warning['message']}", fg=typer.colors.YELLOW)
            for fmt, path in outputs.items():
                typer.secho(f"  ✔ {fmt} : {path}", fg=typer.colors.GREEN)
        except Exception as exc:
            typer.secho(f"  ✘ Échec : {exc}", fg=typer.colors.RED, err=True)
            exit_code = 1
    raise typer.Exit(code=exit_code)


@app.command()
def serve(
    host: str = typer.Option(None, "--host", help="Adresse d'écoute (défaut : 127.0.0.1)."),
    port: int = typer.Option(None, "--port", "-p", help="Port (défaut : 8000)."),
    open_browser: bool = typer.Option(
        False, "--open-browser", "-b", help="Ouvre le navigateur automatiquement."
    ),
) -> None:
    """Démarre l'interface web locale."""
    import uvicorn

    settings = get_settings()
    settings.ensure_dirs()
    final_host = host or settings.host
    final_port = port or settings.port

    from .engines import models_ready

    if not models_ready(settings):
        typer.secho(
            "Modèles non détectés : la première conversion téléchargera ~2 Go.\n"
            "Conseil : exécutez « flowmd setup » au préalable.",
            fg=typer.colors.YELLOW,
        )

    # Un serveur flowMD précédent occupe-t-il déjà le port ? Sans ce contrôle,
    # uvicorn échoue et la fenêtre se ferme sans explication, pendant que le
    # navigateur continue de parler à l'ancien serveur (code périmé).
    import socket

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((final_host, final_port))
    except OSError:
        typer.secho(
            f"ERREUR : le port {final_port} est déjà utilisé.\n"
            "Une autre fenêtre flowMD tourne probablement encore (peut-être avec une "
            "ancienne version du code).\n"
            "Fermez-la, ou exécutez dans une invite de commandes :\n"
            "    taskkill /f /im python.exe\n"
            "puis relancez flowMD.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from None
    finally:
        probe.close()

    url = f"http://{final_host}:{final_port}"
    typer.secho(f"flowMD démarre sur {url}", fg=typer.colors.GREEN)
    if open_browser:
        import threading
        import webbrowser

        threading.Timer(1.5, webbrowser.open, args=(url,)).start()

    uvicorn.run("flowmd.server.app:create_app", host=final_host, port=final_port, factory=True)


@app.command()
def setup() -> None:
    """Télécharge tous les modèles (~2 Go) pour un fonctionnement 100 % hors ligne."""
    settings = get_settings()
    from .setup_models import setup_all

    try:
        setup_all(settings, echo=typer.echo)
    except Exception as exc:
        typer.secho(f"Échec du téléchargement des modèles : {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def doctor() -> None:
    """Diagnostic : Python, moteurs OCR, modèles, pandoc, espace disque."""
    settings = get_settings()
    from .engines import (
        docling_available,
        easyocr_available,
        models_ready,
        paddleocr_available,
        probe_tesseract,
    )

    typer.echo(f"flowMD {__version__}")
    typer.echo(f"Python : {sys.version.split()[0]}")
    typer.echo(f"Dossier de données : {settings.data_dir.resolve()}")

    typer.echo(f"docling installé : {'oui' if docling_available() else 'NON'}")
    typer.echo(f"EasyOCR installé : {'oui' if easyocr_available() else 'NON'}")
    typer.echo(
        "PaddleOCR (PP-OCRv6) installé : "
        + ("oui" if paddleocr_available() else "non (pip install paddlepaddle paddleocr)")
    )

    tess = probe_tesseract()
    if tess.available:
        typer.echo(
            f"Tesseract : {tess.version} ({tess.cmd}) — "
            f"langues fr/ar/en : {sorted(tess.langs) or 'AUCUNE (réinstallez avec Arabic + French)'}"
        )
        if tess.tessdata_dir:
            typer.echo(f"  Dossier de langues imposé : {tess.tessdata_dir}")
    else:
        from .engines import _candidate_tesseract_cmds

        typer.echo(
            "Tesseract : introuvable (facultatif — recommandé pour les documents arabe+français).\n"
            "  S'il vient d'être installé : fermez et relancez ce terminal/flowMD.\n"
            "  Sinon : définissez FLOWMD_TESSERACT_CMD=chemin\\vers\\tesseract.exe"
        )
        candidates = _candidate_tesseract_cmds()
        if candidates:
            typer.echo("  Chemins testés sans succès : " + " ; ".join(candidates))
        else:
            typer.echo("  Aucun emplacement candidat trouvé (PATH, dossiers standards, dossier flowMD).")

    typer.echo(f"Modèles Docling téléchargés : {'oui' if models_ready(settings) else 'non (flowmd setup)'}")

    try:
        import pypandoc

        typer.echo(f"pandoc : {pypandoc.get_pandoc_version()}")
    except Exception:
        typer.echo("pandoc : introuvable (export Word indisponible)")

    usage = shutil.disk_usage(Path.cwd())
    typer.echo(f"Espace disque libre : {usage.free / 1e9:.1f} Go")


if __name__ == "__main__":
    app()
