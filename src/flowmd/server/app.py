"""Application FastAPI : API REST + interface web statique (SPA)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..config import get_settings
from ..jobs import JobStore
from .routes import router

_STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_dirs()

    app = FastAPI(title="flowMD", version=__version__, docs_url="/api/docs")
    app.state.settings = settings
    app.state.job_store = JobStore(settings)

    # Autorise le serveur de dev Vite (npm run dev) pendant le développement.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    if _STATIC_DIR.is_dir() and (_STATIC_DIR / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            candidate = (_STATIC_DIR / full_path).resolve()
            if (
                full_path
                and candidate.is_file()
                and candidate.is_relative_to(_STATIC_DIR.resolve())
            ):
                return FileResponse(candidate)
            return FileResponse(_STATIC_DIR / "index.html")

    return app
