"""Routes REST de flowMD."""

from __future__ import annotations

import io
import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from .. import __version__
from ..config import Settings
from ..engines import engines_status, probe_tesseract
from ..exporters import normalize_formats
from ..jobs import JobStore
from ..languages import LanguageError, normalize_langs, plan_ocr
from .schemas import ErrorOut, JobOut, PreviewOut

router = APIRouter(prefix="/api")

_CHUNK = 1024 * 1024


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorOut(code=code, message=message).model_dump())


def _store(request: Request) -> JobStore:
    return request.app.state.job_store


def _settings(request: Request) -> Settings:
    return request.app.state.settings


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/engines")
def engines(request: Request) -> dict:
    return engines_status(_settings(request))


@router.post("/jobs")
async def create_job(
    request: Request,
    files: list[UploadFile],
    langs: str = Form("fr,en"),
    formats: str = Form("md,docx,xlsx"),
    engine: str = Form("auto"),
    force_ocr: bool = Form(False),
):
    settings = _settings(request)
    store = _store(request)
    store.cleanup_expired()

    if not files:
        return _error(400, "NO_FILES", "Aucun fichier reçu.")

    try:
        formats_list = normalize_formats(formats)
        tess = probe_tesseract()
        plan = plan_ocr(engine, normalize_langs(langs), tess.available, tess.langs)
    except (LanguageError, ValueError) as exc:
        return _error(400, "INVALID_PARAMS", str(exc))

    max_file = settings.max_upload_mb * 1024 * 1024
    max_batch = settings.max_batch_mb * 1024 * 1024

    job_id = store.new_job_id()
    upload_dir = store.job_upload_dir(job_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    def fail(status_code: int, code: str, message: str) -> JSONResponse:
        shutil.rmtree(upload_dir, ignore_errors=True)
        return _error(status_code, code, message)

    saved: list[tuple[str, Path]] = []
    total = 0
    for upload in files:
        name = Path(upload.filename or "document.pdf").name
        if not name.lower().endswith(".pdf"):
            return fail(400, "NOT_A_PDF", f"« {name} » n'est pas un fichier PDF.")
        dest = upload_dir / f"{uuid.uuid4().hex[:8]}_{name}"
        size = 0
        with dest.open("wb") as fh:
            while chunk := await upload.read(_CHUNK):
                size += len(chunk)
                total += len(chunk)
                if size > max_file:
                    return fail(
                        413,
                        "FILE_TOO_LARGE",
                        f"« {name} » dépasse la limite de {settings.max_upload_mb} Mo par fichier.",
                    )
                if total > max_batch:
                    return fail(
                        413,
                        "BATCH_TOO_LARGE",
                        f"L'envoi dépasse la limite totale de {settings.max_batch_mb} Mo.",
                    )
                fh.write(chunk)
        saved.append((name, dest))

    job = store.create_job(plan, formats_list, force_ocr, saved, job_id=job_id)
    return JobOut.from_job(job).model_dump()


@router.get("/jobs/{job_id}")
def get_job(request: Request, job_id: str) -> dict:
    job = _store(request).get(job_id)
    if job is None:
        raise HTTPException(404, "Job introuvable.")
    return JobOut.from_job(job).model_dump()


@router.delete("/jobs/{job_id}")
def delete_job(request: Request, job_id: str) -> dict:
    if not _store(request).delete(job_id):
        raise HTTPException(404, "Job introuvable.")
    return {"deleted": job_id}


def _find_task(store: JobStore, job_id: str, file_id: str):
    job = store.get(job_id)
    if job is None:
        raise HTTPException(404, "Job introuvable.")
    for task in job.files:
        if task.id == file_id:
            return job, task
    raise HTTPException(404, "Fichier introuvable dans ce job.")


@router.get("/jobs/{job_id}/files/{file_id}/preview")
def preview(request: Request, job_id: str, file_id: str) -> PreviewOut:
    _, task = _find_task(_store(request), job_id, file_id)
    md_path = task.outputs.get("md")
    if md_path is None or not Path(md_path).is_file():
        # le markdown est toujours généré en interne, même si non demandé
        stem = Path(task.original_name).stem or "document"
        candidate = _store(request).job_output_dir(job_id) / stem / f"{stem}.md"
        if not candidate.is_file():
            raise HTTPException(404, "Aperçu non disponible.")
        md_path = candidate
    return PreviewOut(
        file_id=task.id,
        name=task.original_name,
        markdown=Path(md_path).read_text(encoding="utf-8"),
    )


_MEDIA_TYPES = {
    "md": "text/markdown; charset=utf-8",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


@router.get("/jobs/{job_id}/files/{file_id}/download/{fmt}")
def download(request: Request, job_id: str, file_id: str, fmt: str):
    _, task = _find_task(_store(request), job_id, file_id)
    path = task.outputs.get(fmt)
    if path is None or not Path(path).is_file():
        raise HTTPException(404, f"Sortie « {fmt} » non disponible pour ce fichier.")
    stem = Path(task.original_name).stem or "document"
    return FileResponse(
        path,
        media_type=_MEDIA_TYPES.get(fmt, "application/octet-stream"),
        filename=f"{stem}.{fmt}",
    )


@router.get("/jobs/{job_id}/download.zip")
def download_zip(request: Request, job_id: str):
    store = _store(request)
    job = store.get(job_id)
    if job is None:
        raise HTTPException(404, "Job introuvable.")

    out_root = store.job_output_dir(job_id)
    buffer = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for task in job.files:
            for path in task.outputs.values():
                path = Path(path)
                if path.is_file():
                    archive.write(path, arcname=str(path.relative_to(out_root)))
                    count += 1
            # inclure les images extraites référencées par le markdown
            stem = Path(task.original_name).stem or "document"
            images_dir = out_root / stem / f"{stem}_images"
            if images_dir.is_dir():
                for img in sorted(images_dir.rglob("*")):
                    if img.is_file():
                        archive.write(img, arcname=str(img.relative_to(out_root)))
    if count == 0:
        raise HTTPException(404, "Aucune sortie à télécharger pour ce job.")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="flowmd_{job_id}.zip"'},
    )
