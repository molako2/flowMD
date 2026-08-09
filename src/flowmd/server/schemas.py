"""Schémas Pydantic de l'API flowMD."""

from __future__ import annotations

from pydantic import BaseModel

from ..jobs import FileTask, Job


class WarningOut(BaseModel):
    code: str
    message: str


class FileOut(BaseModel):
    id: str
    name: str
    status: str
    page_count: int
    outputs: list[str]
    warnings: list[WarningOut]
    error: str | None = None

    @classmethod
    def from_task(cls, task: FileTask) -> FileOut:
        return cls(
            id=task.id,
            name=task.original_name,
            status=task.status.value,
            page_count=task.page_count,
            outputs=sorted(task.outputs.keys()),
            warnings=[WarningOut(**w) for w in task.warnings],
            error=task.error,
        )


class JobOut(BaseModel):
    id: str
    status: str
    engine: str
    langs: list[str]
    formats: list[str]
    force_ocr: bool
    files: list[FileOut]
    warnings: list[WarningOut]

    @classmethod
    def from_job(cls, job: Job) -> JobOut:
        return cls(
            id=job.id,
            status=job.status,
            engine=job.plan.engine,
            langs=job.plan.langs,
            formats=job.formats,
            force_ocr=job.force_ocr,
            files=[FileOut.from_task(task) for task in job.files],
            warnings=[WarningOut(**w) for w in job.plan.warnings],
        )


class PreviewOut(BaseModel):
    file_id: str
    name: str
    markdown: str


class ErrorOut(BaseModel):
    code: str
    message: str
