"""Tests du complètement automatique des langues Tesseract."""

import io
from types import SimpleNamespace

from flowmd.config import Settings
from flowmd.setup_models import download_tesseract_langs


def _fake_urlopen_factory(payload: bytes):
    class _Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def _urlopen(url, timeout=0):
        return _Response(payload)

    return _urlopen


class TestDownloadTesseractLangs:
    def test_downloads_missing_langs(self, monkeypatch, tmp_path):
        exe = tmp_path / "tesseract.exe"
        exe.write_bytes(b"")
        tessdata = tmp_path / "tessdata"
        tessdata.mkdir()

        import flowmd.engines as engines_module

        monkeypatch.setattr(
            engines_module,
            "probe_tesseract",
            lambda: SimpleNamespace(available=True, cmd=str(exe), langs={"en", "fr"}),
        )
        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen_factory(b"fake-model"))

        messages: list[str] = []
        download_tesseract_langs(Settings(data_dir=tmp_path / "data"), echo=messages.append)

        assert (tessdata / "ara.traineddata").read_bytes() == b"fake-model"
        assert not (tessdata / "fra.traineddata").exists()  # fr déjà présent
        assert any("ara" in m for m in messages)

    def test_noop_without_tesseract(self, monkeypatch, tmp_path):
        import flowmd.engines as engines_module

        monkeypatch.setattr(
            engines_module,
            "probe_tesseract",
            lambda: SimpleNamespace(available=False, cmd=None, langs=set()),
        )
        messages: list[str] = []
        download_tesseract_langs(Settings(data_dir=tmp_path / "data"), echo=messages.append)
        assert messages == []

    def test_noop_when_all_langs_present(self, monkeypatch, tmp_path):
        exe = tmp_path / "tesseract.exe"
        exe.write_bytes(b"")
        import flowmd.engines as engines_module

        monkeypatch.setattr(
            engines_module,
            "probe_tesseract",
            lambda: SimpleNamespace(available=True, cmd=str(exe), langs={"fr", "ar", "en"}),
        )
        messages: list[str] = []
        download_tesseract_langs(Settings(data_dir=tmp_path / "data"), echo=messages.append)
        assert messages == []
