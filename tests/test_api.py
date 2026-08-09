"""Tests de l'API FastAPI avec un pipeline factice (aucun modèle requis)."""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import flowmd.jobs as jobs_module
from flowmd.config import get_settings
from flowmd.jobs import FileStatus


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOWMD_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    def fake_process_file(task, job, settings, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        task.page_count = 3
        task.status = FileStatus.EXPORTING
        stem = Path(task.original_name).stem or "document"
        outputs = {}
        (out_dir / f"{stem}.md").write_text("# Titre\n\nContenu تقرير", encoding="utf-8")
        for fmt in job.formats:
            path = out_dir / f"{stem}.{fmt}"
            if fmt != "md":
                path.write_bytes(b"fake-binary")
            outputs[fmt] = path
        task.outputs = outputs

    monkeypatch.setattr(jobs_module, "process_file", fake_process_file)

    from flowmd.server.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def _wait_done(client: TestClient, job_id: str, timeout: float = 10.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"/api/jobs/{job_id}").json()
        if data["status"] in ("done", "error"):
            return data
        time.sleep(0.05)
    raise AssertionError("le job n'a pas terminé à temps")


def _upload(client: TestClient, **form):
    files = [("files", ("rapport.pdf", b"%PDF-1.4 fake content", "application/pdf"))]
    data = {"langs": "fr,en", "formats": "md,docx,xlsx", "engine": "easyocr", **form}
    return client.post("/api/jobs", files=files, data=data)


class TestHealthAndEngines:
    def test_health(self, client):
        body = client.get("/api/health").json()
        assert body["status"] == "ok"

    def test_engines(self, client):
        body = client.get("/api/engines").json()
        ids = {e["id"] for e in body["engines"]}
        assert {"auto", "easyocr", "tesseract"} <= ids
        assert "models_ready" in body


class TestJobLifecycle:
    def test_full_flow(self, client):
        response = _upload(client)
        assert response.status_code == 200, response.text
        job = response.json()
        assert job["engine"] == "easyocr"

        done = _wait_done(client, job["id"])
        assert done["status"] == "done"
        file_out = done["files"][0]
        assert file_out["status"] == "done"
        assert set(file_out["outputs"]) == {"md", "docx", "xlsx"}
        assert file_out["page_count"] == 3

        preview = client.get(f"/api/jobs/{job['id']}/files/{file_out['id']}/preview")
        assert preview.status_code == 200
        assert "Titre" in preview.json()["markdown"]

        download = client.get(
            f"/api/jobs/{job['id']}/files/{file_out['id']}/download/docx"
        )
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("application/vnd.openxml")

        zip_response = client.get(f"/api/jobs/{job['id']}/download.zip")
        assert zip_response.status_code == 200
        assert zip_response.headers["content-type"] == "application/zip"

        delete = client.delete(f"/api/jobs/{job['id']}")
        assert delete.status_code == 200
        assert client.get(f"/api/jobs/{job['id']}").status_code == 404

    def test_easyocr_ar_fr_warning_surfaced(self, client, monkeypatch):
        from flowmd.engines import TesseractInfo

        monkeypatch.setattr(
            "flowmd.server.routes.probe_tesseract", lambda: TesseractInfo(available=False)
        )
        response = _upload(client, langs="ar,fr", engine="easyocr")
        assert response.status_code == 200
        job = response.json()
        assert job["langs"] == ["ar"] or job["langs"] == ["ar", "en"]
        assert any(w["code"] == "AR_FR_DROPPED_FR" for w in job["warnings"])

    def test_rejects_non_pdf(self, client):
        files = [("files", ("virus.exe", b"MZ", "application/octet-stream"))]
        response = client.post("/api/jobs", files=files, data={})
        assert response.status_code == 400
        assert response.json()["code"] == "NOT_A_PDF"

    def test_rejects_bad_language(self, client):
        response = _upload(client, langs="klingon")
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_PARAMS"

    def test_unknown_job_404(self, client):
        assert client.get("/api/jobs/nope").status_code == 404
