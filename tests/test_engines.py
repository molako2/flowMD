"""Tests de la détection du binaire Tesseract (cas Windows hors PATH)."""

import shutil
from types import SimpleNamespace

import flowmd.engines as engines_module
from flowmd.engines import _candidate_tesseract_cmds


def _fake_settings(cmd=None):
    return SimpleNamespace(tesseract_cmd=cmd)


class TestCandidateTesseractCmds:
    def test_configured_cmd_has_priority(self, monkeypatch):
        monkeypatch.setattr(
            engines_module, "get_settings", lambda: _fake_settings("C:/Outils/tesseract.exe")
        )
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/tesseract")
        candidates = _candidate_tesseract_cmds()
        assert candidates[0] == "C:/Outils/tesseract.exe"
        assert "/usr/bin/tesseract" in candidates

    def test_path_lookup_when_no_setting(self, monkeypatch):
        monkeypatch.setattr(engines_module, "get_settings", lambda: _fake_settings(None))
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/tesseract")
        assert _candidate_tesseract_cmds()[0] == "/usr/bin/tesseract"

    def test_deduplication(self, monkeypatch):
        monkeypatch.setattr(
            engines_module, "get_settings", lambda: _fake_settings("/usr/bin/tesseract")
        )
        monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/tesseract")
        assert _candidate_tesseract_cmds().count("/usr/bin/tesseract") == 1

    def test_empty_when_nothing_found(self, monkeypatch):
        monkeypatch.setattr(engines_module, "get_settings", lambda: _fake_settings(None))
        monkeypatch.setattr(shutil, "which", lambda _: None)
        monkeypatch.setattr(engines_module.sys, "platform", "linux")
        assert _candidate_tesseract_cmds() == []

    def test_windows_standard_locations(self, monkeypatch, tmp_path):
        exe = tmp_path / "Tesseract-OCR" / "tesseract.exe"
        exe.parent.mkdir()
        exe.write_bytes(b"")
        monkeypatch.setattr(engines_module, "get_settings", lambda: _fake_settings(None))
        monkeypatch.setattr(shutil, "which", lambda _: None)
        monkeypatch.setattr(engines_module.sys, "platform", "win32")
        monkeypatch.setenv("ProgramFiles", str(tmp_path))
        monkeypatch.delenv("ProgramFiles(x86)", raising=False)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        assert _candidate_tesseract_cmds() == [str(exe)]
