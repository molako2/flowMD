"""File de jobs en mémoire + exécuteur mono-thread (conversions CPU lourdes).

Un seul worker : les conversions s'enchaînent sans saturer la RAM d'un
portable, et le cache de convertisseurs Docling reste utilisé par un seul
thread à la fois.
"""

from __future__ import annotations

import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .config import Settings
from .exporters import export_all
from .languages import OcrPlan
from .pipeline import convert_pdf, count_pages


class FileStatus(str, Enum):
    PENDING = "pending"
    CONVERTING = "converting"
    EXPORTING = "exporting"
    DONE = "done"
    ERROR = "error"


@dataclass
class FileTask:
    id: str
    original_name: str
    input_path: Path
    status: FileStatus = FileStatus.PENDING
    page_count: int = 0
    outputs: dict[str, Path] = field(default_factory=dict)
    warnings: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None


@dataclass
class Job:
    id: str
    created_at: float
    plan: OcrPlan
    formats: list[str]
    force_ocr: bool
    files: list[FileTask] = field(default_factory=list)
    finished_at: float | None = None

    @property
    def status(self) -> str:
        statuses = {f.status for f in self.files}
        if statuses <= {FileStatus.DONE, FileStatus.ERROR}:
            if statuses == {FileStatus.ERROR}:
                return "error"
            return "done"
        if statuses == {FileStatus.PENDING}:
            return "pending"
        return "processing"


def process_file(task: FileTask, job: Job, settings: Settings, out_dir: Path) -> None:
    """Convertit puis exporte un fichier. Levé d'exception = fichier en erreur.

    Fonction module-level volontairement : les tests la remplacent (monkeypatch)
    pour exécuter l'API sans modèles.
    """
    result = convert_pdf(task.input_path, job.plan, settings, force_ocr=job.force_ocr)
    task.page_count = result.page_count
    task.warnings.extend(result.warnings)
    task.status = FileStatus.EXPORTING

    stem = Path(task.original_name).stem or "document"
    metadata = {
        "source": task.original_name,
        "engine": job.plan.engine,
        "langs": job.plan.langs,
        "pages": result.page_count,
    }
    outputs, warnings = export_all(result.document, job.formats, out_dir, stem, metadata)
    task.outputs = outputs
    task.warnings.extend(warnings)


class JobStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="flowmd-worker")

    # -- cycle de vie -----------------------------------------------------

    def new_job_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def create_job(
        self,
        plan: OcrPlan,
        formats: list[str],
        force_ocr: bool,
        files: list[tuple[str, Path]],
        job_id: str | None = None,
    ) -> Job:
        job_id = job_id or self.new_job_id()
        job = Job(
            id=job_id,
            created_at=time.time(),
            plan=plan,
            formats=formats,
            force_ocr=force_ocr,
        )
        for original_name, path in files:
            task = FileTask(
                id=uuid.uuid4().hex[:8],
                original_name=original_name,
                input_path=path,
                page_count=count_pages(path),
            )
            task.warnings.extend(plan.warnings)
            job.files.append(task)
        with self._lock:
            self._jobs[job_id] = job
        self._executor.submit(self._run_job, job_id)
        return job

    def _run_job(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is None:
            return
        for task in job.files:
            out_dir = self.job_output_dir(job_id) / (Path(task.original_name).stem or task.id)
            task.status = FileStatus.CONVERTING
            try:
                process_file(task, job, self._settings, out_dir)
                task.status = FileStatus.DONE
            except Exception as exc:
                task.status = FileStatus.ERROR
                task.error = str(exc)
        job.finished_at = time.time()

    # -- accès -------------------------------------------------------------

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def job_output_dir(self, job_id: str) -> Path:
        return self._settings.outputs_dir / job_id

    def job_upload_dir(self, job_id: str) -> Path:
        return self._settings.uploads_dir / job_id

    # -- nettoyage ----------------------------------------------------------

    def delete(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job is None:
            return False
        shutil.rmtree(self.job_output_dir(job_id), ignore_errors=True)
        shutil.rmtree(self.job_upload_dir(job_id), ignore_errors=True)
        return True

    def cleanup_expired(self) -> int:
        ttl = self._settings.job_ttl_hours * 3600
        now = time.time()
        expired = [
            job.id
            for job in self.list_jobs()
            if job.finished_at is not None and now - job.finished_at > ttl
        ]
        for job_id in expired:
            self.delete(job_id)
        return len(expired)
